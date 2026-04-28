
"""
Static, legal, feedback, and analytics pages.

This file handles legal pages, accessibility, donations, feedback intake,
staff analytics, and the custom 404/500 error pages.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Q

# Import only the models needed here
from core.models import Document, Course, UserProfile, Report, Feedback, Notification, Community
from django.core.paginator import Paginator
from core.models import Notification
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth import get_user_model

User = get_user_model()


# ==========================================
# 1. Informational and static pages
# ==========================================

def terms_view(request):
    return render(request, 'core/terms.html')

def donations(request):
    return render(request, 'core/donations.html')

def accessibility_view(request):
    return render(request, 'core/accessibility.html')

def privacy_view(request):
    return render(request, 'core/privacy.html')


# ==========================================
# 2. System, feedback, and analytics
# ==========================================

def submit_feedback(request):
    if request.method == 'POST':
        screenshot = request.FILES.get('screenshot')
        Feedback.objects.create(
            user=request.user if request.user.is_authenticated else None,
            subject=request.POST.get('subject'),
            message=request.POST.get('message'),
            screenshot=screenshot
        )
        messages.success(request, 'תודה על הפידבק! ההודעה נשלחה בהצלחה.')
        return redirect('home')
    return render(request, 'core/feedback.html')


@login_required
def analytics_dashboard(request):
    if not request.user.is_staff:
        return redirect('home')

    # --- יבוא של מודלים נוספים שנצטרך לחישובים ---
    from django.utils import timezone
    from datetime import timedelta
    from core.models import SearchLog, AccountDeletionLog, DownloadLog
    # ----------------------------------------------

    # 1. חישובי זמנים (היום, השבוע, החודש)
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)
    month_start = today_start - timedelta(days=30)

    # 2. משתמשים פעילים (DAU/MAU) וצמיחה
    total_registered_users = User.objects.count()
    dau = User.objects.filter(last_login__gte=today_start).count() # Active Today
    mau = User.objects.filter(last_login__gte=month_start).count() # Active This Month

    new_users_today = User.objects.filter(date_joined__gte=today_start).count()
    new_users_week = User.objects.filter(date_joined__gte=week_start).count()
    new_users_month = User.objects.filter(date_joined__gte=month_start).count()
    deleted_accounts_total = AccountDeletionLog.objects.count()

    # 3. מדד הוויראליות (Referral Success)
    total_profiles = UserProfile.objects.count()
    referred_users_count = UserProfile.objects.filter(referred_by__isnull=False).count()
    referral_percentage = round((referred_users_count / total_profiles * 100), 1) if total_profiles > 0 else 0

    # 4. מעקב קבצים (כמה עלו היום/שבוע/חודש)
    total_files_count = Document.objects.count()
    files_today = Document.objects.filter(upload_date__gte=today_start).count()
    files_week = Document.objects.filter(upload_date__gte=week_start).count()
    files_month = Document.objects.filter(upload_date__gte=month_start).count()

    # 5. מעורבות קהילות ומסלולים
    # נשלוף את 5 הקהילות עם הכי הרבה חברים
    top_communities = Community.objects.annotate(member_count=Count('members')).order_by('-member_count')[:5]

    # 6. מדדי חיפושים (Search & Value)
    recent_searches = SearchLog.objects.filter(created_at__gte=week_start)
    top_searches = recent_searches.values('search_query') \
                       .annotate(search_count=Count('search_query')) \
                       .order_by('-search_count')[:10]

    dead_ends = recent_searches.filter(result_count=0).values('search_query') \
                    .annotate(search_count=Count('search_query')) \
                    .order_by('-search_count')[:10]

    # 7. נתונים קיימים ששדרגנו (סוגי קבצים והורדות טרנדיות)
    pdf_count = Document.objects.filter(file__icontains='.pdf').count()
    word_count = Document.objects.filter(Q(file__icontains='.doc') | Q(file__icontains='.docx')).count()
    other_count = total_files_count - (pdf_count + word_count)

    trending_docs = Document.objects.filter(downloads__download_date__gte=week_start) \
                        .annotate(recent_downloads=Count('downloads')) \
                        .order_by('-recent_downloads')[:5]

    context = {
        # --- משתמשים וצמיחה ---
        'total_users': total_registered_users,
        'dau': dau,
        'mau': mau,
        'new_users_today': new_users_today,
        'new_users_week': new_users_week,
        'new_users_month': new_users_month,
        'deleted_accounts_total': deleted_accounts_total,

        # --- ויראליות ---
        'referred_users_count': referred_users_count,
        'referral_percentage': referral_percentage,

        # --- קבצים ---
        'total_files': total_files_count,
        'files_today': files_today,
        'files_week': files_week,
        'files_month': files_month,

        # --- קהילות ---
        'top_communities': top_communities,

        # --- מדדי תוכן וחיפוש ---
        'top_searches': top_searches,
        'dead_ends': dead_ends,
        'trending_docs': trending_docs,

        # --- נתונים כלליים וותיקים ---
        'total_downloads': Document.objects.aggregate(Sum('download_count'))['download_count__sum'] or 0,
        'total_views': Course.objects.aggregate(Sum('view_count'))['view_count__sum'] or 0,
        'pending_reports': Report.objects.filter(is_resolved=False).order_by('-created_at'),
        'major_distribution': UserProfile.objects.values('major__name').annotate(count=Count('id')).order_by('-count'),
        'pdf_count': pdf_count,
        'word_count': word_count,
        'other_count': other_count,
    }

    return render(request, 'core/analytics.html', context)


# ==========================================
# 3. System error pages
# ==========================================

def error_404(request, exception):
    return render(request, '404.html', status=404)

def error_500(request):
    return render(request, '500.html', status=500)


@login_required
def notifications_list(request):
    current_filter = request.GET.get('filter', 'all')
    all_notifications = Notification.objects.filter(user=request.user).order_by('-created_at')

    # סינון לפי הלוגיקה של הכפתורים שלך
    if current_filter == 'economy':
        all_notifications = all_notifications.filter(notification_type='economy')
    elif current_filter == 'social':
        all_notifications = all_notifications.filter(notification_type='system')

    # סימון כנקרא
    unread = all_notifications.filter(is_read=False)
    if unread.exists():
        unread.update(is_read=True)

    # דפדוף (Pagination) - חשוב כדי שהעמוד לא יטען לאט כ שיהיו 100 התראות
    paginator = Paginator(all_notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'core/notifications_list.html', {
        'page_obj': page_obj,
        'current_filter': current_filter
    })


@login_required
def resolve_notification(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    
    if notification.content_object and hasattr(notification.content_object, 'get_absolute_url'):
        return redirect(notification.content_object.get_absolute_url())
    elif notification.link:
        return redirect(notification.link)
    else:
        return redirect('profile')


@login_required
def report_document(request, document_id):
    if request.method == 'POST':
        doc = get_object_or_404(Document, id=document_id)
        reason = request.POST.get('reason')
        description = request.POST.get('description', '')

        # יצירת הדיווח במסד הנתונים
        report = Report.objects.create(
            document=doc,
            user=request.user,
            reason=reason,
            description=description
        )

        # אם מדובר בזכויות יוצרים - מפעילים את כל ה"אזעקות"
        if reason == 'copyright':
            admins = User.objects.filter(is_staff=True)
            admin_emails = [admin.email for admin in admins if admin.email]

            # 1. יצירת התראה במערכת לכל אדמין
            for admin in admins:
                Notification.objects.create(
                    user=admin,
                    notification_type='system',
                    title="🚨 דיווח דחוף: זכויות יוצרים",
                    message=f"הקובץ '{doc.title}' דווח כהפרת זכויות יוצרים על ידי {request.user.username}.",
                    link=f"/admin/core/report/{report.id}/change/"
                )

            # 2. שליחת מייל דחוף
            subject = f"🔴 דחוף: הפרת זכויות יוצרים - {doc.title}"
            message = f"""
            שלום אדמין,
            התקבל דיווח על הפרת זכויות יוצרים ב-Student Drive.

            פרטי הקובץ: {doc.title}
            דווח על ידי: {request.user.username}
            פירוט הדיווח: {description}

            יש לטפל בזה בהקדם!
            לטיפול באדמין: {request.build_absolute_uri(f'/admin/core/report/{report.id}/change/')}
            """
            try:
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, admin_emails)
            except Exception as e:
                print(f"Error sending email: {e}")

        return JsonResponse({'success': True, 'message': 'הדיווח התקבל ויטופל בהקדם.'})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=400)