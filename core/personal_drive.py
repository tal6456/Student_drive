from django.shortcuts import render
from django.contrib.auth.decorators import login_required
# ייבוא המודלים בדיוק כפי שהם מופיעים ב-models.py שלך
from .models import Document, DownloadLog, Vote

@login_required
def personal_drive(request):
    user = request.user

    # 1. קבצים שהעליתי
    # במודל Document השדה הוא 'upload_date'
    uploaded_files = Document.objects.filter(uploaded_by=user).order_by('-upload_date')

    # 2. קבצים שהורדתי
    # תיקון: שינינו את השם מ-downloaded_at ל-download_date כדי שיתאים למודל המעודכן
    download_logs = DownloadLog.objects.filter(user=user).select_related('document').order_by('-download_date')

    # 3. קבצים שנתתי להם לייק/דיסלייק
    # במודל Vote השדה הוא 'created_at'
    voted_files = Vote.objects.filter(user=user).select_related('document').order_by('-created_at')

    context = {
        'uploaded_files': uploaded_files,
        'download_logs': download_logs,
        'voted_files': voted_files,
        'page_title': 'הדרייב האישי שלי'
    }

    # מוודא שזה מפנה לקובץ ה-HTML הנכון
    return render(request, 'core/personal_drive.html', context)