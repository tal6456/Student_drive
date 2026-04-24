
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
from core.models import Document, Course, UserProfile, Report, Feedback, Notification
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

    total_files_count = Document.objects.count()
    pdf_count = Document.objects.filter(file__icontains='.pdf').count()
    word_count = Document.objects.filter(Q(file__icontains='.doc') | Q(file__icontains='.docx')).count()
    other_count = total_files_count - (pdf_count + word_count)

    context = {
        'total_files': total_files_count,
        'total_downloads': Document.objects.aggregate(Sum('download_count'))['download_count__sum'] or 0,
        'total_views': Course.objects.aggregate(Sum('view_count'))['view_count__sum'] or 0,
        'total_users': UserProfile.objects.exclude(university__isnull=True).count(),
        'major_distribution': UserProfile.objects.values('major__name').annotate(count=Count('id')).order_by('-count'),
        'top_courses': Course.objects.order_by('-view_count')[:5],
        'top_docs': Document.objects.order_by('-download_count')[:5],
        'pending_reports': Report.objects.filter(is_resolved=False).order_by('-created_at'),
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
def report_document(request, doc_id):
    if request.method == 'POST':
        doc = get_object_or_404(Document, id=doc_id)
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
                    notification_type='system',  # או סוג אדמין אם הגדרת
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