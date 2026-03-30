from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
# ייבוא המודלים - וודא שכולם קיימים ב-models.py
from .models import Document, DownloadLog, Vote, ExternalResource


@login_required
def personal_drive(request):
    user = request.user
    uploaded_files = Document.objects.filter(uploaded_by=user).order_by('-upload_date')

    # הוספת ייחודיות להעלאות
    for doc in uploaded_files:
        doc.unique_row_id = f"up_{doc.id}"

    # שימוש ב-select_related לשיפור ביצועים
    logs_queryset = DownloadLog.objects.filter(user=user).select_related(
        'document__course',
        'document__folder',
        'document__uploaded_by'
    )

    # רשימת הסוגים שמופיעים אצלך בתפריט הקורס
    CONTENT_TYPES = ['הרצאות', 'תרגולים', 'מטלות', 'מבחני עבר', 'חומרי עזר נוספים', 'עמית']

    processed_logs = []
    for log in logs_queryset:
        # יצירת מזהה ייחודי לכל שורה כדי שה-3 נקודות יעבדו
        log.unique_row_id = f"hist_{log.id}"

        # ברירת מחדל אם לא מצאנו סוג ספציפי
        log.top_folder_name = "קבצים כלליים"

        # בדיקת שרשרת התיקיות מלמטה למעלה עם הגנה מ-None
        if log.document and log.document.folder:
            current = log.document.folder
            while current:
                if current.name in CONTENT_TYPES:
                    log.top_folder_name = current.name
                    break
                current = getattr(current, 'parent', None)

        processed_logs.append(log)

    # מיון חובה עם הגנה מ-None כדי ש-regroup ב-HTML יעבוד
    processed_logs.sort(key=lambda x: (
        x.document.course.name if x.document and x.document.course else "ללא קורס",
        x.top_folder_name
    ))

    # שליפת המשאבים החיצוניים עבור הטאב החדש
    external_resources = ExternalResource.objects.filter(user=user).order_by('-created_at')

    voted_files = Vote.objects.filter(user=user).select_related('document').order_by('-created_at')

    context = {
        'uploaded_files': uploaded_files,
        'download_logs': processed_logs,
        'voted_files': voted_files,
        'external_resources': external_resources,  # זה מה שמאפשר לטאב להציג נתונים
    }
    return render(request, 'core/personal_drive.html', context)


# --- פונקציות המשאבים החיצוניים (החדשות) ---

@login_required
def add_external_resource(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        link = request.POST.get('link')
        file = request.FILES.get('file')

        if title:
            ExternalResource.objects.create(
                user=request.user,
                title=title,
                link=link,
                file=file
            )
    return redirect('personal_drive')


@login_required
def delete_external_resource(request, resource_id):
    resource = get_object_or_404(ExternalResource, id=resource_id, user=request.user)
    resource.delete()
    return redirect('personal_drive')


# --- פונקציות המחיקה המקוריות שלך (לא נגעתי) ---

@login_required
def remove_from_history(request, log_id):
    """מסיר את הרישום מההיסטוריה (מהדרייב האישי) בלי למחוק את הקובץ מהאתר"""
    log = get_object_or_404(DownloadLog, id=log_id, user=request.user)
    log.delete()
    return redirect('personal_drive')


@login_required
def delete_my_upload(request, doc_id):
    """מחיקה סופית של קובץ שהמשתמש העלה"""
    doc = get_object_or_404(Document, id=doc_id, uploaded_by=request.user)
    doc.delete()
    return redirect('personal_drive')


@login_required
def update_resource_tag(request):
    if request.method == 'POST':
        res_type = request.POST.get('type')  # 'doc' או 'external'
        res_id = request.POST.get('id')
        new_tag = request.POST.get('tag')

        if res_type == 'doc':
            # מחפשים במסמכים הרגילים
            obj = get_object_or_404(Document, id=res_id)
        else:
            # מחפשים במשאבים החיצוניים
            obj = get_object_or_404(ExternalResource, id=res_id, user=request.user)

        obj.personal_tag = new_tag
        obj.save()

    return redirect('personal_drive')