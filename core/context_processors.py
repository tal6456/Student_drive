from .models import Report, Notification

def global_counts(request):
    """
    מעביר את מספר הדיווחים (למנהלים) ואת מספר ההתראות (למשתמשים) לכל האתר.
    """
    data = {
        'pending_reports_count': 0,
        'unread_notifications_count': 0
    }

    if request.user.is_authenticated:
        # ספירת התראות קבצים שלא נקראו לכל משתמש
        data['unread_notifications_count'] = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()

        # ספירת דיווחים פתוחים (רק למנהלים)
        if request.user.is_staff:
            data['pending_reports_count'] = Report.objects.filter(is_resolved=False).count()

    return data