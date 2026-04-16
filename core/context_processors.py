from .models import Report, Notification

def global_counts(request):
    """Expose report and notification counts across the entire site."""
    data = {
        'pending_reports_count': 0,
        'unread_notifications_count': 0
    }

    if request.user.is_authenticated:
        # Count unread file notifications for the current user
        data['unread_notifications_count'] = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()

        # Count open reports for staff users only
        if request.user.is_staff:
            data['pending_reports_count'] = Report.objects.filter(is_resolved=False).count()

    return data
