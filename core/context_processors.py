from .models import Report

def pending_reports_count(request):
    """
    פונקציה שמעבירה את מספר הדיווחים הפתוחים לכל ה-Templates.
    מוצג רק למשתמשים שהם Staff (מנהלים).
    """
    if request.user.is_authenticated and request.user.is_staff:
        count = Report.objects.filter(is_resolved=False).count()
        return {'pending_reports_count': count}
    return {'pending_reports_count': 0}