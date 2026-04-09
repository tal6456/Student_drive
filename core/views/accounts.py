from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from django.contrib.auth import logout, update_session_auth_hash, get_user_model
from django.contrib.auth.forms import PasswordChangeForm

# ייבוא המודלים והטפסים הרלוונטיים
from core.models import UserProfile, Document, DownloadLog, Notification
from core.forms import UserProfileForm

User = get_user_model()

@login_required
def profile(request):
    uploaded_files = Document.objects.filter(uploaded_by=request.user).select_related('course').order_by('-upload_date')
    voted_files = Document.objects.filter(
        votes__user=request.user,
        votes__value=1
    ).distinct().select_related('course', 'uploaded_by')

    download_logs = DownloadLog.objects.filter(user=request.user).select_related('document__course').order_by('-download_date')

    total_downloads = uploaded_files.aggregate(Sum('download_count'))['download_count__sum'] or 0
    total_likes_received = sum(d.total_likes for d in uploaded_files)

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

            ref_code_session = request.session.get('referral_code')
            if ref_code_session and not user_profile.referred_by:
                try:
                    referrer_profile = UserProfile.objects.get(referral_code=ref_code_session)
                    referrer = referrer_profile.user
                    if referrer != request.user:
                        user_profile.referred_by = referrer
                        user_profile.earn_coins(20)
                        referrer_profile.earn_coins(50)
                        del request.session['referral_code']
                        messages.success(request, f"איזה כיף! קיבלת 20 מטבעות בונוס כי הוזמנת על ידי {referrer.username}")
                except UserProfile.DoesNotExist:
                    pass

            messages.success(request, "הפרופיל הושלם בהצלחה! ברוך הבא לקהילה. ✨")
            return redirect('home')
    else:
        form = UserProfileForm(instance=profile, user=request.user)

    return render(request, 'core/complete_profile.html', {'form': form})


@login_required
def change_password(request):
    has_password = request.user.has_usable_password()

    if request.method == 'POST':
        if not has_password:
            messages.error(request, 'משתמשי גוגל לא יכולים לשנות סיסמה דרך המערכת.')
            return redirect('settings')

        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'הסיסמה שלך שונתה בהצלחה! 🔒')
            return redirect('settings')
        else:
            messages.error(request, 'יש שגיאות בטופס, אנא בדוק את הפרטים.')
    else:
        form = PasswordChangeForm(request.user) if has_password else None

    return render(request, 'core/change_password.html', {
        'form': form,
        'has_password': has_password
    })


@login_required
def request_user_data(request):
    if request.method == 'POST':
        profile = request.user.profile
        profile.last_data_request = timezone.now()
        profile.save()
        messages.success(request, 'בקשתך התקבלה! נרכז עבורך את כל המידע ונשלח לך עותק למייל תוך 48 שעות.')
    return redirect('settings')


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
    delete_id = request.GET.get('delete')
    if delete_id:
        notification = Notification.objects.filter(id=delete_id, user=request.user).first()
        if notification:
            target_url = notification.link
            notification.delete()
            return redirect(target_url)

    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    notifications.filter(is_read=False).update(is_read=True)

    return render(request, 'core/notifications.html', {
        'notifications': notifications
    })