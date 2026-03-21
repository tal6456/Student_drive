from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout, update_session_auth_hash, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Count, Sum, Q
from django.urls import reverse
from django.http import JsonResponse
from django.core.mail import send_mail
from django.contrib import messages
from django.utils import timezone
import datetime
import os
from django.db import models

from .models import (University, Major, Course, Document, UserProfile,
                     Report, Feedback, Folder, Post, MarketplacePost, VideoPost, Comment, Friendship,
                     AcademicStaff, Lecturer, TeachingAssistant, StaffReview, CourseSemesterStaff, Community)

from .forms import CourseForm, UserProfileForm
from .ai_utils import generate_smart_summary

from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt

from django.conf import settings
from django.shortcuts import render

import json
import re
from django.views.decorators.http import require_POST


# שימוש במודל המשתמש החדש בצורה בטוחה
User = get_user_model()


def home(request):
    # 1. הגנה: אם המשתמש לא מחובר, הוא לא רואה את דף הבית אלא מועבר ישר להתחברות
    # הוספנו תנאי שמאפשר לו בכל זאת לראות תוצאות חיפוש או ניווט מוסדות גם בלי להתחבר (אופציונלי)
    # אם אתה רוצה חסימה מוחלטת, תשאיר רק את: if not request.user.is_authenticated: return redirect('account_login')

    search_query = request.GET.get('search', '').strip()
    uni_id = request.GET.get('university')
    major_id = request.GET.get('major')
    year_id = request.GET.get('year')
    browse_all = request.GET.get('browse')

    if not request.user.is_authenticated and not any([search_query, uni_id, major_id, year_id, browse_all]):
        return redirect('account_login')

    # 2. בדיקה האם המשתמש הגיע דרך קישור שיתוף
    ref_code = request.GET.get('ref')
    if ref_code:
        request.session['referral_code'] = ref_code

    if request.user.is_authenticated:
        profile = request.user.profile
        # בודקים אם הפרופיל הושלם
        has_completed_profile = bool(request.user.first_name or profile.university)
        if not has_completed_profile and not request.session.get('onboarding_complete'):
            request.session['onboarding_complete'] = True
            return redirect('complete_profile')

    # הגדרות בסיסיות
    year_names = {1: "שנה א'", 2: "שנה ב'", 3: "שנה ג'", 4: "שנה ד'", 5: "תואר שני"}

    # אלופי הדרייב לצד שמאל
    top_users = UserProfile.objects.filter(
        lifetime_coins__gt=0,
        show_coins_publicly=True
    ).order_by('-lifetime_coins')[:5]

    context = {
        'search_query': search_query,
        'top_users': top_users,
        'years': year_names,
    }
    if request.user.is_authenticated:
        context['favorite_ids'] = request.user.profile.favorite_courses.values_list('id', flat=True)

    # 3. לוגיקת חיפוש
    if search_query:
        courses_results = Course.objects.filter(
            Q(name__icontains=search_query) | Q(course_number__icontains=search_query)
        ).select_related('major__university')

        context['courses_results'] = courses_results
        context['step'] = 'search_results'
        return render(request, 'core/home.html', context)

    # 4. בדיקה האם להציג את עץ המוסדות או את "הסמסטר שלי"
    if any([uni_id, major_id, year_id, browse_all]):
        if uni_id:
            context['selected_uni'] = get_object_or_404(University, id=uni_id)
            context['uni_id'] = uni_id

        if not uni_id:
            context['universities'] = University.objects.all()
            context['step'] = 'select_uni'
        elif uni_id and not major_id:
            context['majors'] = Major.objects.filter(university_id=uni_id)
            context['step'] = 'select_major'
        elif major_id and not year_id:
            context['selected_major'] = get_object_or_404(Major, id=major_id)
            context['step'] = 'select_year'
            context['major_id'] = major_id
        else:
            courses = Course.objects.filter(major_id=major_id, year=year_id)
            context['selected_major'] = get_object_or_404(Major, id=major_id)
            context['sem_a'] = courses.filter(semester='A')
            context['sem_b'] = courses.filter(semester='B')
            context['step'] = 'show_courses'
            context['major_id'] = major_id
            context['year'] = year_id

    else:
        # 5. ברירת מחדל למשתמש מחובר - דף הבית הראשי ("הסמסטר שלי")
        if request.user.is_authenticated:
            context['favorite_courses'] = request.user.profile.favorite_courses.select_related(
                'major__university').all()

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
            staff_id = request.POST.get('staff_member_id')
            new_staff_name = request.POST.get('new_lecturer_name')

            parent_folder = None
            if parent_id and parent_id != 'root':
                parent_folder = get_object_or_404(Folder, id=parent_id, course=course)

            assigned_staff = None
            if new_staff_name and new_staff_name.strip():
                assigned_staff, _ = Lecturer.objects.get_or_create(
                    name=new_staff_name.strip(),
                    university=course.major.university
                )
            elif staff_id:
                assigned_staff = get_object_or_404(AcademicStaff, id=staff_id)

            if folder_name:
                Folder.objects.create(
                    course=course,
                    name=folder_name.strip(),
                    parent=parent_folder,
                    staff_member=assigned_staff,
                    created_by=request.user
                )
                messages.success(request, f'התיקייה "{folder_name}" נוצרה בהצלחה!')

                # --- הקוד החדש ---
            redirect_url = reverse('course_detail', args=[course.id])
            if parent_id and parent_id != 'root':
                redirect_url += f"?open_folder={parent_id}"
            return redirect(redirect_url)

        elif action == 'edit_folder':
            folder_id_raw = request.POST.get('folder_id')
            staff_id_select = request.POST.get('staff_member_id', '')
            new_staff_input = request.POST.get('new_lecturer_name', '')
            folder_color = request.POST.get('folder_color')
            rating_val = request.POST.get('rating', '0')
            review_text = request.POST.get('review_text', '')

            if folder_id_raw:
                clean_id = folder_id_raw.replace('folder_', '')
                folder_to_edit = get_object_or_404(Folder, id=clean_id, course=course)
                final_staff = None

                if new_staff_input and new_staff_input.strip():
                    new_lecturer, _ = Lecturer.objects.get_or_create(
                        name=new_staff_input.strip(),
                        university=course.major.university
                    )
                    final_staff = new_lecturer
                elif staff_id_select and staff_id_select.strip().isdigit():
                    final_staff = get_object_or_404(AcademicStaff, id=staff_id_select.strip())
                folder_to_edit.staff_member = final_staff

                if folder_color:
                    folder_to_edit.color = folder_color
                folder_to_edit.save()

                if final_staff and rating_val.isdigit() and int(rating_val) > 0:
                    rating_int = int(rating_val)
                    if 1 <= rating_int <= 5:
                        review, created = StaffReview.objects.update_or_create(
                            staff_member=final_staff,
                            user=request.user,
                            defaults={'rating': rating_int, 'review_text': review_text.strip()}
                        )
                        avg = final_staff.reviews.aggregate(models.Avg('rating'))['rating__avg']
                        final_staff.average_rating = round(avg, 1)
                        final_staff.save()

                        if created:
                            request.user.profile.earn_coins(2)
                            messages.success(request, 'התיקייה עודכנה, וקיבלת 2 מטבעות על הדירוג! 🪙')
                        else:
                            messages.success(request, 'התיקייה והדירוג שלך עודכנו בהצלחה!')
                else:
                    messages.success(request, 'התיקייה עודכנה בהצלחה!')
            # --- הקוד החדש והמתוקן ---
            redirect_url = reverse('course_detail', args=[course.id])

            # אנחנו אומרים לשרת: תחזור ל"אבא" של התיקייה שערכנו (כדי שנישאר באותו מסך ונראה את השינוי)
            if folder_to_edit.parent:
                redirect_url += f"?open_folder={folder_to_edit.parent.id}"

            return redirect(redirect_url)

        elif action == 'quick_upload':
            uploaded_files = request.FILES.getlist('file')
            folder_id = request.POST.get('folder_id')
            parent_folder = None

            if folder_id and folder_id not in ['root', 'null']:
                parent_folder = get_object_or_404(Folder, id=folder_id, course=course)

            from .utils import GLOBAL_MAX_FILE_SIZE_MB, GLOBAL_ALLOWED_DOCUMENTS, GLOBAL_ALLOWED_IMAGES

            uploaded_count = 0

            for uploaded_file in uploaded_files:
                ext = os.path.splitext(uploaded_file.name)[1].lower()

                # בדיקת משקל מקסימלי (20MB)
                if uploaded_file.size > GLOBAL_MAX_FILE_SIZE_MB * 1024 * 1024:
                    return JsonResponse({
                        'success': False,
                        'error': f'הקובץ "{uploaded_file.name}" שוקל מעל {GLOBAL_MAX_FILE_SIZE_MB}MB. אנא כווץ אותו ונסה שוב.'
                    })

                # מוודא רק שזה קובץ חוקי מהרשימה שלנו (בלי מגבלת מינימום!)
                if ext in GLOBAL_ALLOWED_DOCUMENTS or ext in GLOBAL_ALLOWED_IMAGES:
                    assigned_staff = parent_folder.staff_member if parent_folder else None
                    Document.objects.create(
                        course=course, folder=parent_folder,
                        title=os.path.splitext(uploaded_file.name)[0],
                        file=uploaded_file, staff_member=assigned_staff,
                        uploaded_by=request.user
                    )
                    request.user.profile.earn_coins(1)
                    uploaded_count += 1

            if uploaded_count > 0:
                return JsonResponse({'success': True, 'message': f'הועלו {uploaded_count} קבצים בהצלחה.'})
            else:
                return JsonResponse(
                    {'success': False, 'error': 'הקובץ נדחה. אנא העלה רק סוגי קבצים נתמכים.'})

    all_folders = Folder.objects.filter(course=course)
    all_documents = Document.objects.filter(course=course).order_by('-upload_date')

    context = {
        'course': course,
        'folders': all_folders,
        'documents': all_documents,
        'uni_lecturers': AcademicStaff.objects.filter(university=course.major.university).order_by('name'),
    }
    return render(request, 'core/course_detail.html', context)


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
            request.user.profile.earn_coins(5)
            messages.success(request, 'הקורס נוסף בהצלחה! קיבלת 5 מטבעות דרייב 🪙')
            return redirect('course_detail', course_id=c.id)
    else:
        form = CourseForm(initial={'major': request.GET.get('major_id'), 'year': request.GET.get('year')})
    return render(request, 'core/add_course.html', {'form': form})


def lecturers_index(request):
    uid = request.GET.get('university')
    staff_members = AcademicStaff.objects.filter(university_id=uid) if uid else AcademicStaff.objects.all()
    staff_members = staff_members.order_by('-average_rating')

    for staff in staff_members:
        staff.display_name = staff.privacy_name

    return render(request, 'core/lecturers_index.html', {
        'staff_members': staff_members,
        'universities': University.objects.all(),
        'selected_uni': get_object_or_404(University, id=uid) if uid else None
    })


def staff_detail(request, staff_id):
    staff = get_object_or_404(AcademicStaff, id=staff_id)
    reviews = staff.reviews.all().order_by('-created_at')

    total = reviews.count()
    ratings_dist = {i: {'count': reviews.filter(rating=i).count(),
                        'percentage': (reviews.filter(rating=i).count() / total * 100 if total > 0 else 0)}
                    for i in range(1, 6)}

    courses = Course.objects.filter(
        Q(semester_staff__staff_member=staff) | Q(folders__staff_member=staff)
    ).distinct()

    return render(request, 'core/staff_detail.html', {
        'staff': staff,
        'display_name': staff.privacy_name,
        'reviews': reviews,
        'ratings_dist': ratings_dist,
        'courses': courses,
    })


@login_required
def rate_staff(request, staff_id):
    if request.method == 'POST':
        staff = get_object_or_404(AcademicStaff, id=staff_id)
        rating = int(request.POST.get('rating', 0))
        text = request.POST.get('review_text', '')

        if 1 <= rating <= 5:
            review, created = StaffReview.objects.update_or_create(
                staff_member=staff, user=request.user,
                defaults={'rating': rating, 'review_text': text}
            )
            avg = staff.reviews.aggregate(models.Avg('rating'))['rating__avg']
            staff.average_rating = round(avg, 1)
            staff.save()

            if created:
                request.user.profile.earn_coins(2)
            messages.success(request, 'הדירוג עודכן בהצלחה! ✨')
    return redirect('staff_detail', staff_id=staff.id)


def terms_view(request): return render(request, 'core/terms.html')


def donations(request): return render(request, 'core/donations.html')


@login_required
def download_file(request, document_id):
    d = get_object_or_404(Document, id=document_id)
    d.download_count += 1
    d.save()
    return redirect(d.file.url)


@login_required
def document_viewer(request, document_id):
    """
    מכין את הקובץ לתצוגה חכמה בתוך האתר (Google Docs Viewer / PDF / תמונה)
    """
    document = get_object_or_404(Document, id=document_id)

    # חילוץ הסיומת בלי הנקודה
    ext = document.file_extension.replace('.', '').lower()
    file_type = 'other'

    if ext in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
        file_type = 'image'
    elif ext == 'pdf':
        file_type = 'pdf'
    elif ext in ['doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx']:
        file_type = 'office'

    context = {
        'document': document,
        'file_type': file_type,
        # Google Docs Viewer חייב קישור מלא (כולל https והדומיין)
        'absolute_file_url': request.build_absolute_uri(document.file.url)
    }
    return render(request, 'core/document_viewer.html', context)

# הוסף את זה מעל הפונקציה כדי לבדוק אם זו בעיית אבטחה
@login_required
def summarize_document_ai(request, document_id):
    d, p = get_object_or_404(Document, id=document_id), request.user.profile
    is_admin = request.user.is_staff or request.user.is_superuser

    # if not is_admin:
    #     if p.current_balance < 5:
    #         return JsonResponse({'success': False, 'error': 'אין לך מספיק מטבעות!'})

    s = generate_smart_summary(d)

    if "שגיאה" not in s:
        # if not is_admin:
        #     p.spend_coins(5)
        return JsonResponse({'success': True, 'summary': s, 'new_coins': p.current_balance})

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


def error_404(request, exception): return render(request, '404.html', status=404)


def error_500(request): return render(request, '500.html', status=500)


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
            CourseSemesterStaff.objects.update_or_create(course=c, academic_year=y, semester=s,
                                                         defaults={'staff_member': lec})
            messages.success(request, 'המרצה שויך בהצלחה לסמסטר!')
    return redirect('course_detail', course_id=course_id)


@login_required
def community_feed(request):
    profile = request.user.profile
    if not profile.university:
        messages.info(request, "כדי לראות קהילות מותאמות אישית, מומלץ לבחור מוסד לימודים בפרופיל.")

    my_communities = request.user.joined_communities.all()

    community_id = request.GET.get('community')
    if community_id:
        current_community = get_object_or_404(Community, id=community_id)
    else:
        # --- יצירת קהילה חכמה אם היא חסרה ---
        if profile.university:
            current_community, created = Community.objects.get_or_create(
                university=profile.university,
                community_type='university',
                defaults={
                    'name': f'קהילת {profile.university.name}',
                    'description': 'הקהילה הרשמית לסטודנטים במוסד זה.'
                }
            )
        else:
            current_community, created = Community.objects.get_or_create(
                community_type='global',
                defaults={
                    'name': 'הקהילה הגלובלית',
                    'description': 'קהילת כלל הסטודנטים בישראל.'
                }
            )

        # מוודאים שהמשתמש חבר בקהילה שמצאנו/יצרנו
        if current_community not in my_communities:
            current_community.members.add(request.user)

    posts = Post.objects.filter(community=current_community).select_related('user',
                                                                            'user__profile') if current_community else Post.objects.none()

    post_filter = request.GET.get('type')
    if post_filter == 'market':
        posts = posts.filter(marketplacepost__isnull=False)

    posts = posts.order_by('-created_at')

    if request.method == 'POST':
        content = request.POST.get('content')
        post_type = request.POST.get('post_type')

        target_community_id = request.POST.get('target_community')
        target_community = get_object_or_404(Community,
                                             id=target_community_id) if target_community_id else current_community

        if not target_community:
            messages.error(request, "עליך להיות חבר בקהילה כדי לפרסם פוסט.")
            return redirect('community_feed')

        if content:
            if post_type == 'market':
                MarketplacePost.objects.create(
                    user=request.user, content=content, community=target_community,
                    university=profile.university, category=request.POST.get('category'),
                    price=request.POST.get('price') or None
                )
            elif post_type == 'video':
                # אנחנו משתמשים ב-POST במקום FILES, ושומרים את זה לשדה החדש youtube_url
                VideoPost.objects.create(
                    user=request.user,
                    content=content,
                    community=target_community,
                    university=profile.university,
                    youtube_url=request.POST.get('youtube_url')
                )
            else:
                Post.objects.create(
                    user=request.user, content=content, community=target_community,
                    university=profile.university, image=request.FILES.get('image')
                )

            messages.success(request, f"הפוסט פורסם ב{target_community.name}! ✨")
            return redirect(f"{reverse('community_feed')}?community={target_community.id}")

    suggested_communities = Community.objects.filter(university=profile.university).exclude(
        members=request.user).order_by('?')[:3] if profile.university else Community.objects.none()

    context = {
        'posts': posts,
        'my_communities': my_communities,
        'current_community': current_community,
        'suggested_communities': suggested_communities,
        'university': profile.university,
    }
    return render(request, 'core/community_feed.html', context)


def public_profile(request, username):
    target_user = get_object_or_404(User, username=username)
    target_profile = target_user.profile

    if target_profile.profile_visibility == 'private' and request.user != target_user:
        messages.warning(request, "פרופיל זה הוא פרטי.")
        return redirect('home')

    user_posts = Post.objects.filter(user=target_user).order_by('-created_at')
    user_documents = Document.objects.filter(uploaded_by=target_user).order_by('-upload_date')

    friendship_status = 'none'
    friend_request_id = None

    if request.user.is_authenticated and request.user != target_user:
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
                    friendship_status = 'request_sent'
                else:
                    friendship_status = 'request_received'

    context = {
        'target_user': target_user,
        'target_profile': target_profile,
        'posts': user_posts,
        'documents': user_documents,
        'friendship_status': friendship_status,
        'friend_request_id': friend_request_id,
    }
    return render(request, 'core/public_profile.html', context)


@login_required
def like_post(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id)
        if request.user in post.likes.all():
            post.likes.remove(request.user)
            liked = False
        else:
            post.likes.add(request.user)
            liked = True
        return JsonResponse({'liked': liked, 'total_likes': post.likes.count()})
    return JsonResponse({'error': 'בקשה לא חוקית. נדרש POST.'}, status=400)


@login_required
def send_friend_request(request, username):
    user_to = get_object_or_404(User, username=username)
    if request.user == user_to:
        messages.warning(request, "אי אפשר לשלוח בקשת חברות לעצמך.")
        return redirect('public_profile', username=username)

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
    friend_req = get_object_or_404(Friendship, id=request_id, user_to=request.user, status='pending')
    friend_req.status = 'accepted'
    friend_req.save()
    messages.success(request, f"איזה כיף! אתה ו-{friend_req.user_from.username} עכשיו חברים.")
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
def reject_friend_request(request, request_id):
    friend_req = get_object_or_404(Friendship, id=request_id, user_to=request.user, status='pending')
    friend_req.delete()
    messages.info(request, "בקשת החברות נמחקה.")
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
def global_search(request):
    query = request.GET.get('q', '').strip()
    users, documents, courses, lecturers, folders = [], [], [], [], []

    if query:
        if request.user.is_authenticated:
            users = User.objects.filter(username__icontains=query).exclude(id=request.user.id)[:10]
        else:
            users = User.objects.filter(username__icontains=query)[:10]

        documents = Document.objects.filter(
            Q(title__icontains=query) | Q(course__name__icontains=query)).select_related('course', 'uploaded_by')[:10]
        courses = Course.objects.filter(Q(name__icontains=query) | Q(course_number__icontains=query)).select_related(
            'major')[:10]
        lecturers = Lecturer.objects.filter(name__icontains=query)[:10]
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


@login_required
def like_document(request, document_id):
    if request.method == 'POST':
        doc = get_object_or_404(Document, id=document_id)
        if request.user in doc.likes.all():
            doc.likes.remove(request.user)
            liked = False
        else:
            doc.likes.add(request.user)
            liked = True

            # מערכת התגמולים האמיתית: מי שמעלה תוכן איכותי מקבל מטבעות!
            # מוודאים שהמשתמש לא עושה לייק לעצמו כדי לרמות את המערכת
            if doc.uploaded_by and doc.uploaded_by != request.user:
                doc.uploaded_by.profile.earn_coins(1)

        return JsonResponse({'liked': liked, 'total_likes': doc.total_likes})
    return JsonResponse({'error': 'בקשה לא חוקית'}, status=400)


@login_required
def my_friends(request):
    friends = request.user.profile.get_accepted_friends
    return render(request, 'core/friends_list.html', {'friends': friends})


@login_required
def remove_friend(request, friend_username):
    friend_user = get_object_or_404(User, username=friend_username)
    Friendship.objects.filter(
        (models.Q(user_from=request.user, user_to=friend_user) |
         models.Q(user_from=friend_user, user_to=request.user)),
        status='accepted'
    ).delete()
    messages.success(request, f"הסרת את {friend_username} מרשימת החברים שלך.")
    return redirect('my_friends')


@login_required
def complete_profile(request):
    profile = request.user.profile

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile, user=request.user)
        if form.is_valid():
            user_profile = form.save()

            # העדכון שמחלץ ממעגל החסימה!
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
                        messages.success(request,
                                         f"איזה כיף! קיבלת 20 מטבעות בונוס כי הוזמנת על ידי {referrer.username}")
                except UserProfile.DoesNotExist:
                    pass

            messages.success(request, "הפרופיל הושלם בהצלחה! ברוך הבא לקהילה. ✨")
            return redirect('home')
    else:
        form = UserProfileForm(instance=profile, user=request.user)

    return render(request, 'core/complete_profile.html', {'form': form})


@login_required
def toggle_favorite_course(request, course_id):
    if request.method == 'POST':
        course = get_object_or_404(Course, id=course_id)
        profile = request.user.profile
        if course in profile.favorite_courses.all():
            profile.favorite_courses.remove(course)
            is_favorite = False
        else:
            profile.favorite_courses.add(course)
            is_favorite = True
        return JsonResponse({'is_favorite': is_favorite})
    return JsonResponse({'error': 'בקשה לא חוקית'}, status=400)


@login_required
def join_community(request, community_id):
    community = get_object_or_404(Community, id=community_id)
    community.members.add(request.user)
    messages.success(request, f"ברוך הבא ל{community.name}! הקהילה נוספה לפיד שלך.")
    return redirect(f"{reverse('community_feed')}?community={community.id}")


@login_required
def discover_communities(request):
    query = request.GET.get('q', '')
    all_communities = Community.objects.all()
    if query:
        all_communities = all_communities.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    context = {
        'global_comm': all_communities.filter(community_type='global'),
        'uni_comm': all_communities.filter(community_type='university'),
        'major_comm': all_communities.filter(community_type='major'),
        'query': query,
        'my_community_ids': request.user.joined_communities.values_list('id', flat=True)
    }
    return render(request, 'core/discover_communities.html', context)


@login_required
def add_comment(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id)
        text = request.POST.get('text', '').strip()
        if text:
            comment = Comment.objects.create(post=post, user=request.user, text=text)
            user_img = None
            if hasattr(request.user, 'profile') and request.user.profile.profile_picture:
                user_img = request.user.profile.profile_picture.url
            return JsonResponse({
                'success': True,
                'username': comment.user.username,
                'text': comment.text,
                'created_at': 'עכשיו',
                'user_img': user_img
            })
        return JsonResponse({'success': False, 'error': 'לא ניתן לפרסם תגובה ריקה.'}, status=400)
    return JsonResponse({'success': False, 'error': 'בקשה לא חוקית. נדרש POST.'}, status=400)


@staff_member_required
def agent_report(request):
    """
    מציג את דו"ח ה-AI הסודי רק למנהלי המערכת.
    קורא את הקובץ שנוצר על ידי ה-run_agent בתהליך ה-Build.
    """
    file_path = os.path.join(settings.BASE_DIR, 'PROJECT_MIRROR.md')

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        content = "# ❌ שגיאה\nקובץ התיעוד עדיין לא נוצר. המתן לסיום ה-Build ב-Render."

    return render(request, 'core/agent_report.html', {'report_content': content})


def normalize_string_for_comparison(text):
    """
    פונקציית עזר לניקוי מחרוזות למניעת כפילויות.
    הופכת ' Ben-Gurion ' ל-'ben gurion'.
    """
    if not text:
        return ""
    # הורדת רווחים מהצדדים ואותיות קטנות
    text = text.strip().lower()
    # החלפת מקפים וקווים תחתונים ברווח
    text = re.sub(r'[-_]+', ' ', text)
    # צמצום מספר רווחים עוקבים לרווח אחד
    text = re.sub(r'\s+', ' ', text)
    return text


@require_POST
def add_university_ajax(request):
    """
    נקודת קצה (Endpoint) להוספת מוסד חדש דינמית.
    """
    try:
        data = json.loads(request.body)
        new_name = data.get('name', '').strip()

        if not new_name:
            return JsonResponse({'success': False, 'error': 'שם המוסד לא יכול להיות ריק.'})

        normalized_new_name = normalize_string_for_comparison(new_name)

        # בדיקת כפילויות חכמה מול כל המוסדות
        for uni in University.objects.all():
            if normalize_string_for_comparison(uni.name) == normalized_new_name:
                return JsonResponse({
                    'success': False,
                    'error': f'מוסד זה כבר קיים במערכת בשם "{uni.name}". אנא בחר אותו מהרשימה.'
                })

        # אם עברנו את כל הבדיקות - נייצר מוסד חדש!
        # שים לב: אנחנו שומרים את השם המקורי שהמשתמש הזין (new_name), לא את המנורמל
        new_uni = University.objects.create(name=new_name)

        return JsonResponse({'success': True, 'id': new_uni.id, 'name': new_uni.name})

    except Exception as e:
        return JsonResponse({'success': False, 'error': 'אירעה שגיאה בשרת. נסה שוב.'})


@require_POST
def add_major_ajax(request):
    """
    נקודת קצה (Endpoint) להוספת מסלול חדש דינמית, משויך למוסד ספציפי.
    """
    try:
        data = json.loads(request.body)
        new_name = data.get('name', '').strip()
        uni_id = data.get('university_id')

        if not new_name or not uni_id:
            return JsonResponse({'success': False, 'error': 'חסרים נתונים ליצירת המסלול.'})

        try:
            university = University.objects.get(id=uni_id)
        except University.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'המוסד שנבחר אינו תקין.'})

        normalized_new_name = normalize_string_for_comparison(new_name)

        # בדיקת כפילויות חכמה - רק בתוך המוסד הספציפי שנבחר
        for major in Major.objects.filter(university=university):
            if normalize_string_for_comparison(major.name) == normalized_new_name:
                return JsonResponse({
                    'success': False,
                    'error': f'המסלול כבר קיים במוסד זה בשם "{major.name}".'
                })

        # יצירת המסלול החדש
        new_major = Major.objects.create(name=new_name, university=university)

        return JsonResponse({'success': True, 'id': new_major.id, 'name': new_major.name})

    except Exception as e:
        return JsonResponse({'success': False, 'error': 'אירעה שגיאה בשרת. נסה שוב.'})


# ==========================================
# מערכת מחיקות גלובלית (AJAX)
# ==========================================
@login_required
@require_POST
def delete_item_ajax(request):
    """
    נקודת קצה חכמה למחיקת פריטים מהאתר.
    מקבלת את סוג הפריט וה-ID שלו, בודקת הרשאות מול utils.py, ומוחקת אם מותר.
    """
    try:
        # תמיכה גם ב-JSON וגם ב-FormData
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            item_type = data.get('type')
            item_id = data.get('id')
        else:
            item_type = request.POST.get('type')
            item_id = request.POST.get('id')

        if not item_type or not item_id:
            return JsonResponse({'success': False, 'error': 'חסרים נתונים למחיקה.'})

        # 1. משיכת האובייקט ממסד הנתונים
        obj = None
        if item_type == 'document':
            obj = get_object_or_404(Document, id=item_id)
        elif item_type == 'folder':
            obj = get_object_or_404(Folder, id=item_id)
        elif item_type == 'post':
            obj = get_object_or_404(Post, id=item_id)
        elif item_type == 'comment':
            obj = get_object_or_404(Comment, id=item_id)
        else:
            return JsonResponse({'success': False, 'error': 'סוג פריט לא נתמך.'})

        # 2. קריאה למוח ההרשאות המרכזי שלנו
        from .utils import check_deletion_permission
        is_allowed, error_msg = check_deletion_permission(request.user, obj, item_type)

        # 3. ביצוע המחיקה
        if is_allowed:
            obj.delete()
            return JsonResponse({'success': True, 'message': 'הפריט נמחק בהצלחה.'})
        else:
            return JsonResponse({'success': False, 'error': error_msg})

    except Exception as e:
        return JsonResponse({'success': False, 'error': f'אירעה שגיאה בשרת: {str(e)}'})