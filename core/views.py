from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Count, Sum , Q
from django.urls import reverse
from django.http import JsonResponse
from django.core.mail import send_mail
from django.contrib import messages
from django.utils import timezone
import datetime
import os
from django.db import models
from .models import (University, Major, Course, Document, UserProfile,
    Report, Lecturer, LecturerReview, CourseSemesterLecturer, Feedback, Folder,
    Post, MarketplacePost, VideoPost, Comment, Friendship) # הוספנו את המודלים החדשים

from .forms import CourseForm, UserProfileForm
from .ai_utils import generate_smart_summary

from django.contrib.auth.models import User

from django.http import JsonResponse

from django.contrib.admin.views.decorators import staff_member_required

# ייבוא ה-Decorator שמשחרר את חסימת ה-CSRF לבקשות JS
from django.views.decorators.csrf import csrf_exempt


def home(request):
    # בדיקה האם המשתמש הגיע דרך קישור שיתוף
    ref_code = request.GET.get('ref')
    if ref_code:
        # שומרים את הקוד ב-Session (זיכרון זמני של הדפדפן)
        request.session['referral_code'] = ref_code
    if request.user.is_authenticated:
        profile = request.user.profile
        if not (profile.university and profile.major and profile.year):
            return redirect('complete_profile')

    search_query = request.GET.get('search')
    uni_id = request.GET.get('university')
    major_id = request.GET.get('major')
    year_id = request.GET.get('year')
    browse_all = request.GET.get('browse')

    if request.user.is_authenticated and not any([search_query, uni_id, major_id, year_id, browse_all]):
        profile = request.user.profile
        if profile.university and profile.major and profile.year:
            uni_id = profile.university.id
            major_id = profile.major.id
            year_id = profile.year

    year_names = {1: "שנה א'", 2: "שנה ב'", 3: "שנה ג'", 4: "שנה ד'", 5: "תואר שני"}

    top_users = UserProfile.objects.filter(
        drive_coins__gt=0,
        show_coins_publicly=True
    ).order_by('-drive_coins')[:5]

    context = {
        'search_query': search_query,
        'top_users': top_users,
        'courses': Course.objects.all()
    }

    if uni_id:
        context['selected_uni'] = get_object_or_404(University, id=uni_id)
    if major_id:
        context['selected_major'] = get_object_or_404(Major, id=major_id)
    if year_id:
        try:
            context['selected_year_name'] = year_names[int(year_id)]
        except (ValueError, KeyError):
            context['selected_year_name'] = ""

    if search_query:
        context['courses'] = Course.objects.filter(name__icontains=search_query)
        context['step'] = 'show_courses'
        return render(request, 'core/home.html', context)

    if not uni_id:
        context['universities'] = University.objects.all()
        context['step'] = 'select_uni'
    elif uni_id and not major_id:
        context['majors'] = Major.objects.filter(university_id=uni_id)
        context['step'] = 'select_major'
        context['uni_id'] = uni_id
    elif major_id and not year_id:
        context['years'] = year_names
        context['step'] = 'select_year'
        context['major_id'] = major_id
        context['uni_id'] = uni_id
    else:
        courses = Course.objects.filter(major_id=major_id, year=year_id)
        context['sem_a'] = courses.filter(semester='A', track='general')
        context['sem_b'] = courses.filter(semester='B', track='general')
        context['specializations'] = courses.exclude(track='general').order_by('track')
        context['step'] = 'show_courses'
        context['major_id'] = major_id
        context['year'] = year_id
        context['uni_id'] = uni_id

    return render(request, 'core/home.html', context)


def live_search(request):
    query = request.GET.get('q', '')
    if len(query) >= 2:
        courses = Course.objects.select_related('major__university').filter(name__icontains=query)[:8]
        results = []
        for course in courses:
            uni = course.major.university
            results.append({
                'id': course.id,
                'name': course.name,
                'major': course.major.name,
                'university': uni.name,
                'brand_color': uni.brand_color,
                'logo_url': uni.logo.url if uni.logo else None,
                'url': reverse('course_detail', args=[course.id])
            })
        return JsonResponse({'results': results})
    return JsonResponse({'results': []})


@login_required
def settings_view(request):
    profile = request.user.profile
    if request.method == 'POST':
        # --- 1. עדכון תמונת פרופיל ---
        # אנחנו בודקים אם הקובץ קיים ב-request.FILES
        if 'profile_picture' in request.FILES:
            profile.profile_picture = request.FILES['profile_picture']

        # --- 2. הגדרות תצוגה ושפה ---
        theme = request.POST.get('theme_preference')
        language = request.POST.get('language_preference')
        if theme: profile.theme_preference = theme
        if language: profile.language_preference = language

        # --- 3. הגדרות פרטיות ואבטחה ---
        profile.show_coins_publicly = request.POST.get('show_coins_publicly') == 'on'
        profile.default_anonymous_upload = request.POST.get('default_anonymous_upload') == 'on'

        visibility = request.POST.get('profile_visibility')
        if visibility in dict(UserProfile.VISIBILITY_CHOICES).keys():
            profile.profile_visibility = visibility

        # שמירה סופית של כל השינויים למסד הנתונים
        profile.save()

        messages.success(request, 'הפרופיל וההגדרות שלך עודכנו בהצלחה! ✨')
        return redirect('settings')

    return render(request, 'core/settings.html')


# --- פונקציות GDPR חדשות ---
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
def change_password(request):
    # בדיקה חכמה: האם למשתמש יש בכלל סיסמה? (אם הוא של גוגל, זה יהיה False)
    has_password = request.user.has_usable_password()

    if request.method == 'POST':
        if not has_password:
            messages.error(request, 'משתמשי גוגל לא יכולים לשנות סיסמה דרך המערכת.')
            return redirect('settings')

        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # חשוב: מעדכן את ה-Session כדי שהמשתמש לא יזרק החוצה אחרי שינוי הסיסמה
            update_session_auth_hash(request, user)
            messages.success(request, 'הסיסמה שלך שונתה בהצלחה! 🔒')
            return redirect('settings')
        else:
            messages.error(request, 'יש שגיאות בטופס, אנא בדוק את הפרטים.')
    else:
        # טוען את הטופס רק אם למשתמש יש סיסמה, אחרת מעביר None
        form = PasswordChangeForm(request.user) if has_password else None

    return render(request, 'core/change_password.html', {
        'form': form,
        'has_password': has_password
    })


def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    course.view_count += 1
    course.save()

    if request.method == 'POST':
        if not request.user.is_authenticated:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'אנא התחבר למערכת'})
            return redirect('account_login')

        action = request.POST.get('action')

        if action == 'create_folder':
            folder_name = request.POST.get('folder_name')
            parent_id = request.POST.get('parent_folder')
            lecturer_id = request.POST.get('lecturer')
            new_lecturer_name = request.POST.get('new_lecturer_name')

            parent_folder = None
            if parent_id and parent_id != 'root':
                parent_folder = get_object_or_404(Folder, id=parent_id, course=course)

            assigned_lecturer = None
            if new_lecturer_name and new_lecturer_name.strip():
                assigned_lecturer, created = Lecturer.objects.get_or_create(
                    name=new_lecturer_name.strip(),
                    university=course.major.university
                )
            elif lecturer_id:
                assigned_lecturer = get_object_or_404(Lecturer, id=lecturer_id)

            if folder_name:
                Folder.objects.create(
                    course=course,
                    name=folder_name.strip(),
                    parent=parent_folder,
                    lecturer=assigned_lecturer,
                    created_by=request.user
                )
                messages.success(request, f'התיקייה "{folder_name}" נוצרה בהצלחה!')
            return redirect('course_detail', course_id=course.id)

        elif action == 'edit_folder':
            folder_id_raw = request.POST.get('folder_id')
            new_name = request.POST.get('folder_name')
            lecturer_id = request.POST.get('lecturer')
            new_lecturer_name = request.POST.get('new_lecturer_name')

            if folder_id_raw:
                clean_folder_id = folder_id_raw.replace('folder_', '')
                folder_to_edit = get_object_or_404(Folder, id=clean_folder_id, course=course)

                if new_name:
                    folder_to_edit.name = new_name.strip()

                if new_lecturer_name and new_lecturer_name.strip():
                    folder_to_edit.lecturer, _ = Lecturer.objects.get_or_create(
                        name=new_lecturer_name.strip(),
                        university=course.major.university
                    )
                elif lecturer_id:
                    folder_to_edit.lecturer = get_object_or_404(Lecturer, id=lecturer_id)
                else:
                    folder_to_edit.lecturer = None

                folder_to_edit.save()
                messages.success(request, 'התיקייה עודכנה בהצלחה!')
            return redirect('course_detail', course_id=course.id)

        elif action == 'quick_upload':
            uploaded_files = request.FILES.getlist('file')
            folder_id = request.POST.get('folder_id')
            parent_folder = None

            if folder_id and folder_id != 'root' and folder_id != 'null':
                parent_folder = get_object_or_404(Folder, id=folder_id, course=course)

            # בדיקת הגדרות הפרטיות של המשתמש - האם מעלה אנונימי כברירת מחדל?
            is_anon = request.user.profile.default_anonymous_upload

            for uploaded_file in uploaded_files:
                original_name = os.path.splitext(uploaded_file.name)[0]
                assigned_lecturer = parent_folder.lecturer if parent_folder else None

                Document.objects.create(
                    course=course,
                    folder=parent_folder,
                    title=original_name,
                    file=uploaded_file,
                    lecturer=assigned_lecturer,
                    uploaded_by=request.user,
                    is_anonymous=is_anon  # שימוש בהגדרה החכמה!
                )
                request.user.profile.drive_coins += 1

            request.user.profile.save()

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                messages.success(request, f'{len(uploaded_files)} קבצים הועלו בהצלחה! תודה על התרומה 🪙')
                return JsonResponse({'success': True})

            return redirect('course_detail', course_id=course.id)

    all_folders = Folder.objects.filter(course=course)
    all_documents = Document.objects.filter(course=course).order_by('-upload_date')
    university_lecturers = Lecturer.objects.filter(university=course.major.university).order_by('name')

    context = {
        'course': course,
        'folders': all_folders,
        'documents': all_documents,
        'uni_lecturers': university_lecturers,
    }

    return render(request, 'core/course_detail.html', context)


@login_required
def analytics_dashboard(request):
    # חסימת גישה למי שאינו מנהל (Staff) והפניה שקטה לדף הבית
    if not request.user.is_staff:
        return redirect('home')

    # ספירת סך הקבצים (שומרים במשתנה כדי להשתמש בזה גם לחישוב הגרף)
    total_files_count = Document.objects.count()

    # חישובי נתונים לגרף סוגי הקבצים
    pdf_count = Document.objects.filter(file__icontains='.pdf').count()
    word_count = Document.objects.filter(Q(file__icontains='.doc') | Q(file__icontains='.docx')).count()
    other_count = total_files_count - (pdf_count + word_count)

    context = {
        # הנתונים החכמים המקוריים שלך
        'total_files': total_files_count,
        'total_downloads': Document.objects.aggregate(Sum('download_count'))['download_count__sum'] or 0,
        'total_views': Course.objects.aggregate(Sum('view_count'))['view_count__sum'] or 0,
        'total_users': UserProfile.objects.exclude(university__isnull=True).count(),
        'major_distribution': UserProfile.objects.values('major__name').annotate(count=Count('id')).order_by('-count'),
        'top_courses': Course.objects.order_by('-view_count')[:5],
        'top_docs': Document.objects.order_by('-download_count')[:5],
        'pending_reports': Report.objects.filter(is_resolved=False).order_by('-created_at'),

        # המשתנים החדשים שהוספנו בשביל הגרפים
        'pdf_count': pdf_count,
        'word_count': word_count,
        'other_count': other_count,
    }

    return render(request, 'core/analytics.html', context)


@login_required
def profile(request):
    user_docs = Document.objects.filter(uploaded_by=request.user)
    context = {
        'user_documents': user_docs,
        'liked_documents': request.user.liked_documents.all(),
        'total_downloads': user_docs.aggregate(Sum('download_count'))['download_count__sum'] or 0,
        'total_likes_received': sum(d.total_likes for d in user_docs),
    }
    return render(request, 'core/profile.html', context)


@login_required
def add_course(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            c = form.save()
            request.user.profile.drive_coins += 5
            request.user.profile.save()
            messages.success(request, 'הקורס נוסף בהצלחה! קיבלת 5 מטבעות דרייב 🪙')
            return redirect('course_detail', course_id=c.id)
    else:
        form = CourseForm(initial={'major': request.GET.get('major_id'), 'year': request.GET.get('year')})
    return render(request, 'core/add_course.html', {'form': form})


def lecturers_index(request):
    uid = request.GET.get('university')
    lecs = Lecturer.objects.filter(university_id=uid) if uid else Lecturer.objects.all()
    lecs = sorted(lecs, key=lambda l: l.average_rating, reverse=True)
    return render(request, 'core/lecturers_index.html', {'lecturers': lecs, 'universities': University.objects.all()})


@login_required
def rate_lecturer(request, lecturer_id):
    if request.method == 'POST':
        l = get_object_or_404(Lecturer, id=lecturer_id)
        r, rt = int(request.POST.get('rating', 0)), request.POST.get('review_text', '')
        if 1 <= r <= 5:
            LecturerReview.objects.update_or_create(lecturer=l, user=request.user,
                                                    defaults={'rating': r, 'review_text': rt})
            request.user.profile.drive_coins += 2
            request.user.profile.save()
            messages.success(request, 'הדירוג נשמר! קיבלת 2 מטבעות דרייב 🪙')
    return redirect(f"{reverse('lecturers_index')}?university={l.university.id}")


def terms_view(request): return render(request, 'core/terms.html')


def donations(request): return render(request, 'core/donations.html')


@login_required
def download_file(request, document_id):
    d = get_object_or_404(Document, id=document_id)
    d.download_count += 1
    d.save()
    return redirect(d.file.url)


@login_required
def summarize_document_ai(request, document_id):
    d, p = get_object_or_404(Document, id=document_id), request.user.profile
    if p.drive_coins < 5: return JsonResponse({'success': False, 'error': 'אין לך מספיק מטבעות!'})
    s = generate_smart_summary(d.file.path)
    if "שגיאה" not in s:
        p.drive_coins -= 5
        p.save()
        return JsonResponse({'success': True, 'summary': s, 'new_coins': p.drive_coins})
    return JsonResponse({'success': False, 'error': s})


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
def report_document(request, document_id):
    if request.method == 'POST':
        d = get_object_or_404(Document, id=document_id)
        Report.objects.create(document=d, user=request.user, reason=request.POST.get('reason'),
                              description=request.POST.get('description', ''))
        messages.success(request, 'הדיווח התקבל וייבדק בהקדם על ידי ההנהלה.')
    return redirect('course_detail', course_id=d.course.id)


def accessibility_view(request): return render(request, 'core/accessibility.html')


def privacy_view(request): return render(request, 'core/privacy.html')


def load_majors(request):
    university_id = request.GET.get('university')
    if university_id:
        majors = Major.objects.filter(university_id=university_id).order_by('name')
        return JsonResponse(list(majors.values('id', 'name')), safe=False)
    return JsonResponse([])


def error_404(request, exception):
    return render(request, '404.html', status=404)


def error_500(request):
    return render(request, '500.html', status=500)


@login_required
def set_semester_lecturer(request, course_id):
    if request.method == 'POST':
        c = get_object_or_404(Course, id=course_id)
        y, s = request.POST.get('academic_year'), request.POST.get('semester')
        lid, nln = request.POST.get('lecturer_id'), request.POST.get('new_lecturer_name')
        lec = None
        if nln:
            lec, _ = Lecturer.objects.get_or_create(name=nln.strip(), university=c.major.university)
        elif lid:
            lec = get_object_or_404(Lecturer, id=lid)
        if lec:
            CourseSemesterLecturer.objects.update_or_create(course=c, academic_year=y, semester=s,
                                                            defaults={'lecturer': lec})
            messages.success(request, 'המרצה שויך בהצלחה לסמסטר!')
    return redirect('course_detail', course_id=course_id)


@login_required
def community_feed(request):
    profile = request.user.profile
    # אם המשתמש לא הגדיר אוניברסיטה, נשלח אותו להשלים פרופיל
    if not profile.university:
        messages.info(request, "כדי לראות את הקהילה שלך, אנא בחר מוסד לימודים.")
        return redirect('complete_profile')

    # שליפת כל הפוסטים השייכים לאוניברסיטה של המשתמש
    # אנחנו משתמשים ב-select_related כדי שהאתר יעבוד מהר יותר
    posts = Post.objects.filter(university=profile.university).select_related('user', 'user__profile').order_by(
        '-created_at')

    # טיפול ביצירת פוסט חדש (POST)
    if request.method == 'POST':
        content = request.POST.get('content')
        post_type = request.POST.get('post_type')  # 'normal', 'market', 'video'

        if content:
            if post_type == 'market':
                category = request.POST.get('category')
                price = request.POST.get('price') or None
                MarketplacePost.objects.create(
                    user=request.user, content=content,
                    university=profile.university, major=profile.major,
                    category=category, price=price
                )
            elif post_type == 'video':
                video_file = request.FILES.get('video_file')
                VideoPost.objects.create(
                    user=request.user, content=content,
                    university=profile.university, major=profile.major,
                    video_file=video_file
                )
            else:
                Post.objects.create(
                    user=request.user, content=content,
                    university=profile.university, major=profile.major,
                    image=request.FILES.get('image')
                )

            messages.success(request, "הפוסט פורסם בקהילה! ✨")
            return redirect('community_feed')

    context = {
        'posts': posts,
        'university': profile.university,
        'major': profile.major,
    }
    return render(request, 'core/community_feed.html', context)


def public_profile(request, username):
    # חיפוש המשתמש לפי שם המשתמש שלו
    target_user = get_object_or_404(User, username=username)
    target_profile = target_user.profile

    # בדיקת פרטיות: אם הפרופיל פרטי וזה לא המשתמש עצמו
    if target_profile.profile_visibility == 'private' and request.user != target_user:
        messages.warning(request, "פרופיל זה הוא פרטי.")
        return redirect('home')

    # שליפת הפוסטים והמסמכים של המשתמש הזה
    user_posts = Post.objects.filter(user=target_user).order_by('-created_at')
    user_documents = Document.objects.filter(uploaded_by=target_user, is_anonymous=False)

    # --- תחילת בדיקת מצב החברות המורחבת ---
    friendship_status = 'none'
    friend_request_id = None

    if request.user != target_user:
        relation = Friendship.objects.filter(
            models.Q(user_from=request.user, user_to=target_user) |
            models.Q(user_from=target_user, user_to=request.user)
        ).first()

        if relation:
            friend_request_id = relation.id
            if relation.status == 'accepted':
                friendship_status = 'friends'
            elif relation.status == 'pending':
                if relation.user_from == request.user:
                    friendship_status = 'request_sent'  # אני שלחתי
                else:
                    friendship_status = 'request_received'  # הוא שלח לי
    # --- סוף בדיקת מצב החברות ---

    # מושך את הפוסטים והקבצים של המשתמש (בהנחה שכבר יש לך משהו כזה)
    posts = target_user.posts.all().order_by('-created_at')
    documents = target_user.document_set.all().order_by('-upload_date')

    context = {
        'target_user': target_user,
        'target_profile': target_profile,
        'posts': posts,
        'documents': documents,
        'friendship_status': friendship_status,
        'friend_request_id': friend_request_id,
    }
    return render(request, 'core/public_profile.html', context)


@csrf_exempt
@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.likes.filter(id=request.user.id).exists():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True

    return JsonResponse({'liked': liked, 'total_likes': post.likes.count()})


from django.shortcuts import get_object_or_404
from .models import Friendship


# ==========================================
# מערכת חברים (Friendship)
# ==========================================

@login_required
def send_friend_request(request, username):
    """שליחת בקשת חברות למשתמש אחר"""
    user_to = get_object_or_404(User, username=username)

    # אי אפשר לשלוח לעצמך
    if request.user == user_to:
        messages.warning(request, "אי אפשר לשלוח בקשת חברות לעצמך.")
        return redirect('public_profile', username=username)

    # בדיקה אם כבר יש קשר ביניהם (חברים או ממתין)
    existing_relation = Friendship.objects.filter(
        models.Q(user_from=request.user, user_to=user_to) |
        models.Q(user_from=user_to, user_to=request.user)
    ).first()

    if not existing_relation:
        Friendship.objects.create(user_from=request.user, user_to=user_to, status='pending')
        messages.success(request, f"בקשת חברות נשלחה אל {username}!")
    elif existing_relation.status == 'pending':
        messages.info(request, "כבר קיימת בקשת חברות בהמתנה.")
    else:
        messages.info(request, "אתם כבר חברים!")

    return redirect('public_profile', username=username)


@login_required
def accept_friend_request(request, request_id):
    """אישור בקשת חברות"""
    friend_req = get_object_or_404(Friendship, id=request_id, user_to=request.user, status='pending')
    friend_req.status = 'accepted'
    friend_req.save()
    messages.success(request, f"איזה כיף! אתה ו-{friend_req.user_from.username} עכשיו חברים.")

    # חזרה לדף שממנו המשתמש הגיע
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
def reject_friend_request(request, request_id):
    """דחייה או מחיקה של בקשת חברות"""
    friend_req = get_object_or_404(Friendship, id=request_id, user_to=request.user, status='pending')
    friend_req.delete()
    messages.info(request, "בקשת החברות נמחקה.")

    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
def global_search(request):
    query = request.GET.get('q', '').strip()

    # רשימות ריקות כברירת מחדל
    users, documents, courses, lecturers, folders = [], [], [], [], []

    if query:
        # 1. סטודנטים (לא כולל את מי שמחפש עכשיו)
        if request.user.is_authenticated:
            users = User.objects.filter(username__icontains=query).exclude(id=request.user.id)[:10]

        # 2. קבצים (לפי שם הקובץ או הקורס)
        documents = Document.objects.filter(
            Q(title__icontains=query) | Q(course__name__icontains=query)
        ).select_related('course', 'uploaded_by')[:10]

        # 3. קורסים
        courses = Course.objects.filter(
            Q(name__icontains=query) | Q(course_number__icontains=query)
        ).select_related('major')[:10]

        # 4. מרצים
        lecturers = Lecturer.objects.filter(name__icontains=query)[:10]

        # 5. תיקיות (פיצ'ר חדש לבקשתך!)
        folders = Folder.objects.filter(name__icontains=query).select_related('course')[:10]

    context = {
        'query': query,
        'users': users,
        'documents': documents,
        'courses': courses,
        'lecturers': lecturers,
        'folders': folders,
        'total_results': len(users) + len(documents) + len(courses) + len(lecturers) + len(folders)
    }
    return render(request, 'core/search_results.html', context)


@csrf_exempt
@login_required
def like_document(request, document_id):
    """הוספה או הסרה של לייק לקובץ (AJAX)"""
    if request.method == 'POST':
        doc = get_object_or_404(Document, id=document_id)

        # אם המשתמש כבר עשה לייק - נסיר אותו. אם לא - נוסיף אותו.
        if request.user in doc.likes.all():
            doc.likes.remove(request.user)
            liked = False
        else:
            doc.likes.add(request.user)
            liked = True

        # מחזירים תשובה לדפדפן עם כמות הלייקים העדכנית
        return JsonResponse({
            'liked': liked,
            'total_likes': doc.total_likes
        })

    return JsonResponse({'error': 'בקשה לא חוקית'}, status=400)


@login_required
def my_friends(request):
    """הצגת דף רשימת החברים הייעודי"""
    # אנחנו משתמשים בפרופרטי שיצרנו קודם!
    friends = request.user.profile.get_accepted_friends

    context = {
        'friends': friends,
    }
    return render(request, 'core/friends_list.html', context)


@login_required
def remove_friend(request, friend_username):
    """הסרת חבר מרשימת החברים"""
    friend_user = get_object_or_404(User, username=friend_username)

    # מחפש את קשר החברות ומוחק אותו
    Friendship.objects.filter(
        (models.Q(user_from=request.user, user_to=friend_user) |
         models.Q(user_from=friend_user, user_to=request.user)),
        status='accepted'
    ).delete()

    messages.success(request, f"הסרת את {friend_username} מרשימת החברים שלך.")
    return redirect('my_friends')


@login_required
def complete_profile(request):
    """מסך השלמת הנתונים לאחר הרשמה ראשונית - כולל לוגיקת בונוס והזמנת חברים"""
    profile = request.user.profile

    if request.method == 'POST':
        # אנחנו מעבירים את ה-user לטופס כדי שיוכל למשוך שמות פרטיים ומשפחה
        form = UserProfileForm(request.POST, instance=profile, user=request.user)

        if form.is_valid():
            user_profile = form.save()

            # --- לוגיקת הבונוס (Referral System) ---
            # בודקים האם שמור קוד שיתוף בזיכרון של הדפדפן (מהפונקציה home)
            ref_code_session = request.session.get('referral_code')

            # אם יש קוד וזו הפעם הראשונה שהפרופיל מושלם (אין עדיין referred_by)
            if ref_code_session and not user_profile.referred_by:
                try:
                    # מוצאים את המשתמש שהזמין
                    referrer_profile = UserProfile.objects.get(referral_code=ref_code_session)
                    referrer = referrer_profile.user

                    # מונעים מצב שאדם מזמין את עצמו
                    if referrer != request.user:
                        user_profile.referred_by = referrer
                        user_profile.drive_coins += 20  # בונוס לסטודנט החדש
                        referrer_profile.drive_coins += 50  # בונוס למי שהזמין

                        user_profile.save()
                        referrer_profile.save()

                        # מנקים את הקוד מה-session כדי שלא יופעל שוב
                        del request.session['referral_code']

                        messages.success(request,
                                         f"איזה כיף! קיבלת 20 מטבעות בונוס כי הוזמנת על ידי {referrer.username}")
                except UserProfile.DoesNotExist:
                    pass
            # ---------------------------------------

            messages.success(request, "הפרופיל הושלם בהצלחה! ברוך הבא לקהילה. ✨")
            return redirect('home')
    else:
        form = UserProfileForm(instance=profile, user=request.user)

    return render(request, 'core/complete_profile.html', {'form': form})