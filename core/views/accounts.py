"""
Account and profile views
=========================

This file acts as the user's personal control center.
It handles profile pages, settings, onboarding, password changes,
notifications, and permanent account deletion.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from django.contrib.auth import logout, update_session_auth_hash, get_user_model
from django.contrib.auth.forms import PasswordChangeForm

# Import the relevant models and forms
from core.models import UserProfile, Document, DownloadLog, Notification
from core.forms import UserProfileForm
from core.utils import process_transaction

User = get_user_model()

INVITER_REFERRAL_BONUS = 5
INVITEE_REFERRAL_BONUS = 5

@login_required
def profile(request):
    uploaded_files = Document.objects.filter(uploaded_by=request.user).select_related('course').order_by('-upload_date')
    voted_files = Document.objects.filter(
        votes__user=request.user,
        votes__value=1
    ).distinct().select_related('course', 'uploaded_by')

    download_logs = DownloadLog.objects.filter(user=request.user).select_related('document__course').order_by('-download_date')

    total_downloads = uploaded_files.aggregate(Sum('download_count'))['download_count__sum'] or 0
    total_likes_received = uploaded_files.annotate(num_likes=Count('likes')).aggregate(total=Sum('num_likes'))['total'] or 0

    context = {
        'uploaded_files': uploaded_files,
        'voted_files': voted_files,
        'download_logs': download_logs,
        'total_downloads': total_downloads,
        'total_likes_received': total_likes_received,
    }
    return render(request, 'core/profile.html', context)


@login_required
def settings_view(request):
    profile = request.user.profile
    if request.method == 'POST':
        if 'profile_picture' in request.FILES:
            profile.profile_picture = request.FILES['profile_picture']

        theme = request.POST.get('theme_preference')
        language = request.POST.get('language_preference')
        if theme: profile.theme_preference = theme
        if language: profile.language_preference = language

        profile.show_coins_publicly = request.POST.get('show_coins_publicly') == 'on'

        visibility = request.POST.get('profile_visibility')
        if visibility in dict(UserProfile.VISIBILITY_CHOICES).keys():
            profile.profile_visibility = visibility

        profile.save()
        messages.success(request, 'הפרופיל וההגדרות שלך עודכנו בהצלחה! ✨')
        return redirect('settings')

    return render(request, 'core/settings.html')


@login_required
def complete_profile(request):
    profile = request.user.profile

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile, user=request.user)
        if form.is_valid():
            user_profile = form.save()
            request.session['onboarding_complete'] = True

            # Send notification about 10 starting coins
            Notification.objects.create(
                user=request.user,
                notification_type='coin_bonus',
                title="ברוך הבא! 🎉",
                message="קיבלת 10 מטבעות ראשוניים כמתנה בעל ההרשמה! 🎁",
                link="/wallet/"
            )
            messages.success(request, "🎉 קיבלת 10 מטבעות ראשוניים! בדוק את הארנק שלך.")

            # Handle referral bonus
            ref_code_session = request.session.get('referral_code')
            if ref_code_session and not user_profile.referred_by:
                try:
                    referrer_profile = UserProfile.objects.get(referral_code=ref_code_session)
                    referrer = referrer_profile.user
                    if referrer != request.user:
                        # Set referrer relationship
                        user_profile.referred_by = referrer
                        user_profile.save(update_fields=['referred_by'])

                        # Give bonus to inviter
                        process_transaction(referrer, INVITER_REFERRAL_BONUS, tx_type='referral',
                                            description=f"בונוס חבר-מביא-חבר! ({user_profile.user.username} הצטרף) 🤝",
                                            notify=True)

                        # Give bonus to invited user
                        process_transaction(user_profile.user, INVITEE_REFERRAL_BONUS, tx_type='referral',
                                            description="בונוס הצטרפות דרך קישור הפניה 🎁", notify=True)

                        # Clean up session
                        if 'referral_code' in request.session:
                            del request.session['referral_code']
                        
                        messages.success(request,
                                         f"🎉 אתה קיבלת 5 מטבעות בונוס נוספים! {referrer.username} גם קיבל 5 מטבעות על שהזמין אותך! 💝")
                except UserProfile.DoesNotExist:
                    # Log invalid referral code
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Invalid referral code: {ref_code_session} for user {request.user.username}")
                    if 'referral_code' in request.session:
                        del request.session['referral_code']

            messages.success(request, "הפרופיל הושלם בהצלחה! ברוך הבא לקהילה. ✨")
            return redirect('home')
    else:
        form = UserProfileForm(instance=profile, user=request.user)

    return render(request, 'core/complete_profile.html', {'form': form})


@login_required
def change_password(request):
    has_password = request.user.has_usable_password()
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.method == 'POST':
        if not has_password:
            error_message = 'משתמשי גוגל לא יכולים לשנות סיסמה דרך המערכת.'
            if is_ajax:
                return JsonResponse({'success': False, 'message': error_message}, status=400)
            messages.error(request, error_message)
            return redirect('settings')

        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            success_message = 'הסיסמה שלך שונתה בהצלחה! 🔒'
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': success_message,
                    'redirect_url': reverse('profile')
                })
            messages.success(request, success_message)
            return redirect('profile')
        else:
            if is_ajax:
                errors = {
                    field: [err.get('message', '') for err in error_list]
                    for field, error_list in form.errors.get_json_data().items()
                }
                first_error = next((msgs[0] for msgs in errors.values() if msgs), 'יש שגיאות בטופס, אנא בדוק את הפרטים.')
                return JsonResponse({
                    'success': False,
                    'message': first_error,
                    'errors': errors
                }, status=400)
            messages.error(request, 'יש שגיאות בטופס, אנא בדוק את הפרטים.')
    else:
        form = PasswordChangeForm(request.user) if has_password else None

    return render(request, 'core/change_password.html', {
        'form': form,
        'has_password': has_password
    })

@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        messages.info(request, 'חשבונך נמחק לצמיתות מהמערכת. תודה שהיית חלק מהקהילה! 👋')
        return redirect('home')
    return redirect('settings')


@login_required
def notifications_list(request):
    # 1. מחיקת התראה בודדת (קיים בקוד שלך)
    delete_id = request.GET.get('delete')
    if delete_id:
        notification = Notification.objects.filter(id=delete_id, user=request.user).first()
        if notification:
            target_url = notification.link or 'notifications_list'
            notification.delete()
            return redirect(target_url)

    # 2. סינון לפי סוג (חדש!)
    notif_filter = request.GET.get('filter', 'all')
    notifications = Notification.objects.filter(user=request.user).select_related('sender')

    if notif_filter == 'economy':
        notifications = notifications.filter(notification_type='economy')
    elif notif_filter == 'social':
        notifications = notifications.filter(notification_type__in=['friend_request', 'system'])

    notifications = notifications.order_by('-created_at')

    # 3. עדכון סטטוס "נקרא" (רק מה שמוצג כרגע למשתמש)
    unread_count = notifications.filter(is_read=False).count()
    if unread_count > 0:
        notifications.filter(is_read=False).update(is_read=True)

    context = {
        'notifications': notifications,
        'current_filter': notif_filter,
        'unread_count': unread_count
    }
    return render(request, 'core/notifications.html', context)


@login_required
def wallet_view(request):
    profile = request.user.profile
    # שליפת היסטוריית התנועות, מהחדשה ביותר לישנה
    transactions = request.user.coin_transactions.all().order_by('-created_at')

    context = {
        'profile': profile,
        'transactions': transactions,
    }
    return render(request, 'core/wallet.html', context)