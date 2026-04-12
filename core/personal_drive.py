"""
ניהול האזור האישי של הסטודנט
============================
קובץ זה מנהל את ה"מחסן" הפרטי של כל משתמש באתר.
הוא מאפשר לסטודנט לראות את כל הקבצים שהוא העלה, לצפות בהיסטוריית ההורדות 
שלו ולנהל קישורים חיצוניים פרטיים.
הקוד כאן דואג לסדר את הקבצים לפי הקורסים והתיקיות שלהם באופן אוטומטי, 
ומאפשר למשתמש לנקות את ההיסטוריה או למחוק סופית תכנים שלו.
ולהוסיף משאבים חיצוניים.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
# ייבוא המודלים - ב-models.py
from .models import Document, DownloadLog, Vote, ExternalResource


@login_required
def personal_drive(request):
    user = request.user
    
    # 1. שליפת כל הקבצים שהמשתמש העלה עם select_related לביצועים
    uploaded_files_queryset = Document.objects.filter(uploaded_by=user).select_related('course',
                                                                                       'folder').prefetch_related(
        'likes', 'comments').order_by('-upload_date')
    CONTENT_TYPES = ['הרצאות', 'תרגולים', 'מטלות', 'מבחני עבר', 'חומרי עזר נוספים', 'עמית']
    
    processed_uploads = []
    for doc in uploaded_files_queryset:
        # מזהה ייחודי ל-HTML
        doc.unique_row_id = f"up_{doc.id}"
        
        # לוגיקת זיהוי התיקייה (בדיוק כמו בהיסטוריה!)
        doc.top_folder_name = "קבצים כלליים"
        if doc.folder:
            current = doc.folder
            while current:
                if current.name in CONTENT_TYPES:
                    doc.top_folder_name = current.name
                    break
                current = getattr(current, 'parent', None)
        
        processed_uploads.append(doc)

    # מיון כדי ש-regroup ב-HTML יעבוד נכון (לפי קורס ואז לפי תיקייה)
    processed_uploads.sort(key=lambda x: (
        x.course.name if x.course else "ללא קורס",
        x.top_folder_name
    ))

    # 2. טיפול בהיסטוריית הורדות (הקוד הקיים שלך - נשאר ללא שינוי)
    logs_queryset = DownloadLog.objects.filter(user=user).select_related(
        'document__course',
        'document__folder',
        'document__uploaded_by'
    ).prefetch_related('document__likes', 'document__comments')

    processed_logs = []
    for log in logs_queryset:
        log.unique_row_id = f"hist_{log.id}"
        log.top_folder_name = "קבצים כלליים"
        if log.document and log.document.folder:
            current = log.document.folder
            while current:
                if current.name in CONTENT_TYPES:
                    log.top_folder_name = current.name
                    break
                current = getattr(current, 'parent', None)
        processed_logs.append(log)

    processed_logs.sort(key=lambda x: (
        x.document.course.name if x.document and x.document.course else "ללא קורס",
        x.top_folder_name
    ))

    # משאבים חיצוניים והצבעות
    external_resources = ExternalResource.objects.filter(user=user).order_by('-created_at')
    voted_files = Vote.objects.filter(user=user).select_related('document').order_by('-created_at')

    context = {
        'uploaded_files': processed_uploads, # עכשיו הם מעובדים וממוינים!
        'download_logs': processed_logs,
        'voted_files': voted_files,
        'external_resources': external_resources,
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