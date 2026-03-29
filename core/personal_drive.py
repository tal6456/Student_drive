from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
# ייבוא המודלים בדיוק כפי שהם מופיעים ב-models.py שלך
from .models import Document, DownloadLog, Vote


@login_required
def personal_drive(request):
    user = request.user
    uploaded_files = Document.objects.filter(uploaded_by=user).order_by('-upload_date')

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
        # פתרון הבעיה: יצירת מזהה ייחודי לכל שורה כדי שה-3 נקודות יעבדו
        log.unique_row_id = f"hist_{log.id}"

        # ברירת מחדל אם לא מצאנו סוג ספציפי
        log.top_folder_name = "קבצים כלליים"

        # בדיקת שרשרת התיקיות מלמטה למעלה
        current = log.document.folder
        while current:
            if current.name in CONTENT_TYPES:
                log.top_folder_name = current.name
                break
            current = current.parent

        processed_logs.append(log)

    # מיון חובה כדי ש-regroup ב-HTML יעבוד נכון
    processed_logs.sort(key=lambda x: (x.document.course.name, x.top_folder_name))

    voted_files = Vote.objects.filter(user=user).select_related('document').order_by('-created_at')

    context = {
        'uploaded_files': uploaded_files,
        'download_logs': processed_logs,
        'voted_files': voted_files,
    }
    return render(request, 'core/personal_drive.html', context)


# הפונקציה החדשה למחיקה מההיסטוריה (מטפלת בשגיאה הצהובה שקיבלת)
