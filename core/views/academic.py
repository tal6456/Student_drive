"""
Academic navigation and course views
===================================

This file manages navigation across institutions, global search,
and the organization of study materials inside courses.

It handles:
1. Home and search flows, including hierarchical browsing and live search.
2. Course and folder management, including quick uploads and favorites.
3. Academic staff pages and rating logic.
4. Gamification through Drive coin rewards.
5. Basic onboarding redirects for new users.
"""

import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Avg
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.contrib.auth import get_user_model
from django.views.generic import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

# Import only the models and forms relevant to the academic area
from core.models import (
    University, Major, Course, Folder, Document,
    AcademicStaff, Lecturer, StaffReview, CourseSemesterStaff,
    UserProfile, UserCourseSelection, Comment, DocumentComment
)
from core.forms import CourseForm
from core.utils import get_client_ip, process_transaction, check_daily_limit


User = get_user_model()

class CoursePermissionMixin(LoginRequiredMixin, UserPassesTestMixin):
    model = Course
    pk_url_kwarg = 'course_id'

    def _is_admin(self):
        user = self.request.user
        return user.is_superuser or user.is_staff or getattr(user, 'role', '') == 'admin'

    def handle_no_permission(self):
        messages.error(
            self.request,
            getattr(self, 'permission_denied_message', 'אין לך הרשאה לבצע פעולה זו על הקורס.')
        )
        return redirect('course_detail', course_id=self.get_object().id)


class CourseCreateView(LoginRequiredMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = 'core/add_course.html'

    def get_initial(self):
        initial = super().get_initial()
        initial.update({
            'major': self.request.GET.get('major_id'),
            'year': self.request.GET.get('year'),
        })
        return initial

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.creator = self.request.user
        self.object.save()
        self.object.create_default_folder_tree()
        messages.success(self.request, 'הקורס נוסף בהצלחה! הקהילה מודה לך 📚')
        return redirect('course_detail', course_id=self.object.id)


class CourseUpdateView(CoursePermissionMixin, UpdateView):
    form_class = CourseForm
    template_name = 'core/add_course.html'

    def test_func(self):
        course = self.get_object()
        return self._is_admin() or course.creator_id == self.request.user.id

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit_mode'] = True
        return context

    def form_valid(self, form):
        messages.success(self.request, 'הקורס עודכן בהצלחה.')
        return super().form_valid(form)


class CourseDeleteView(CoursePermissionMixin, DeleteView):
    success_url = reverse_lazy('home')

    def test_func(self):
        course = self.get_object()
        if self._is_admin():
            return True
        if course.creator_id != self.request.user.id:
            self.permission_denied_message = 'רק יוצר הקורס יכול למחוק אותו.'
            return False
        if course.folders.exists() or course.document_set.exists():
            self.permission_denied_message = 'לא ניתן למחוק קורס שמכיל תיקיות או קבצים.'
            return False
        return True

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        course_name = self.object.name
        response = super().post(request, *args, **kwargs)
        messages.success(request, f"הקורס '{course_name}' נמחק בהצלחה.")
        return response

# ==========================================
# 1. Home and search views
# ==========================================

def home(request):
    search_query = request.GET.get('search', '').strip()
    uni_id = request.GET.get('university')
    major_id = request.GET.get('major')
    year_id = request.GET.get('year')
    browse_all = request.GET.get('browse')

    if not request.user.is_authenticated and not any([search_query, uni_id, major_id, year_id, browse_all]):
        return redirect('account_login')

    ref_code = request.GET.get('ref')
    if ref_code:
        request.session['referral_code'] = ref_code

    if request.user.is_authenticated:
        profile = request.user.profile

        # הבדיקה הקשוחה: האם יש טלפון? האם הוזן שם?
        # (אם המשתמש סטודנט, הטופס ב-HTML כבר ידאג שהוא ימלא גם אוניברסיטה)
        has_phone = bool(profile.phone_number)
        has_name = bool(request.user.first_name)

        # אם חסר טלפון או שם, אנחנו לא נותנים לו להמשיך לדף הבית
        if not has_phone or not has_name:
            # אנחנו מסירים את ה-session כדי לוודא שגם אם הוא ניסה לעקוף, הוא יחזור לטופס
            if request.session.get('onboarding_complete'):
                del request.session['onboarding_complete']
            return redirect('complete_profile')

    year_names = {1: "שנה א'", 2: "שנה ב'", 3: "שנה ג'", 4: "שנה ד'", 5: "תואר שני"}

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

    if search_query:
        courses_results = Course.objects.filter(
            Q(name__icontains=search_query) | Q(course_number__icontains=search_query)
        ).select_related('major__university')

        context['courses_results'] = courses_results
        context['step'] = 'search_results'
        return render(request, 'core/home.html', context)

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
            courses = Course.objects.filter(major_id=major_id, year=year_id).select_related('major__university')
            context['selected_major'] = get_object_or_404(Major, id=major_id)
            context['sem_a'] = courses.filter(semester='A')
            context['sem_b'] = courses.filter(semester='B')
            context['sem_summer'] = courses.filter(semester='summer')
            context['sem_yearly'] = courses.filter(semester='yearly')
            context['step'] = 'show_courses'
            context['major_id'] = major_id
            context['year'] = year_id
    else:
        if request.user.is_authenticated:
            context['favorite_courses'] = request.user.profile.favorite_courses.select_related(
                'major__university').all()

    # Handle AJAX requests for browse navigation
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html_content = render_to_string('core/home.html', context, request)
        return JsonResponse({'html': html_content})

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
def global_search(request):
    query = request.GET.get('q', '').strip()
    universities, courses, documents, lecturers = [], [], [], []

    if query:
        # Search institutions and courses
        universities = University.objects.filter(name__icontains=query)[:5]
        query_words = query.split()
        course_q = Q()
        for word in query_words:
            course_q &= (Q(name__icontains=word) | Q(course_number__icontains=word))
        courses = Course.objects.filter(course_q).select_related('major__university')[:15]
        
        # --- Upgrade: search inside extracted file content ---
        documents = Document.objects.filter(
            Q(title__icontains=query) | 
            Q(file_content__icontains=query) |  # Search inside extracted PDF/Word text
            Q(course__name__icontains=query)
        ).select_related('course').distinct()[:15]
        # ------------------------------------------

        lecturers = Lecturer.objects.filter(name__icontains=query)[:10]

    context = {
        'query': query,
        'universities': universities,
        'courses': courses,
        'documents': documents,
        'lecturers': lecturers,
        'total_results': len(universities) + len(courses) + len(documents) + len(lecturers)
    }
    return render(request, 'core/search_results.html', context)

# ==========================================
# 2. Course management
# ==========================================

def course_detail(request, course_id, folder_id=None):
    course = get_object_or_404(Course.objects.select_related('major__university'), id=course_id)
    course.view_count += 1
    course.save()

    open_this_folder = folder_id if folder_id else request.GET.get('open_folder')

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

            if open_this_folder:
                return redirect('course_detail_folder', course_id=course.id, folder_id=open_this_folder)
            return redirect('course_detail', course_id=course.id)

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

                # 1. טיפול בהוספת או שיוך מרצה לתיקייה
                if new_staff_input and new_staff_input.strip():
                    new_lecturer, staff_created = Lecturer.objects.get_or_create(
                        name=new_staff_input.strip(),
                        university=course.major.university
                    )
                    folder_to_edit.staff_member = new_lecturer

                    # בונוס על הוספת מרצה חדש (1 מטבע, עד 2 ביום)
                    if staff_created:
                        new_lecturer.created_by = request.user
                        new_lecturer.save()
                        if check_daily_limit(request.user, 'add_lecturer', 2):
                            process_transaction(request.user, 1, tx_type='system',
                                                description='בונוס על הוספת מרצה חדש 🎓 קיבלת מטבע 1.')

                elif staff_id_select and staff_id_select.strip().isdigit():
                    folder_to_edit.staff_member = get_object_or_404(AcademicStaff, id=staff_id_select.strip())

                # 2. שמירת הצבע והמרצה בתיקייה
                if folder_color:
                    folder_to_edit.color = folder_color
                folder_to_edit.save()

                # 3. טיפול בדירוג מרצה (אם המשתמש לחץ על הכוכבים)
                if folder_to_edit.staff_member and rating_val.isdigit() and int(rating_val) > 0:
                    rating_int = int(rating_val)
                    review, review_created = StaffReview.objects.update_or_create(
                        staff_member=folder_to_edit.staff_member,
                        user=request.user,
                        defaults={'rating': rating_int, 'review_text': review_text.strip()}
                    )

                    # חישוב ממוצע חדש למרצה
                    from django.db.models import Avg
                    avg = folder_to_edit.staff_member.reviews.aggregate(Avg('rating'))['rating__avg']
                    if avg:
                        folder_to_edit.staff_member.average_rating = round(avg, 1)
                        folder_to_edit.staff_member.save()

                        # חלוקת בונוס על דירוג (1 מטבע, עד 2 ביום)
                        if review_created:
                            if check_daily_limit(request.user, 'add_review', 2):
                                process_transaction(request.user, 1, tx_type='quality_bonus',
                                                    description='בונוס על דירוג איש סגל ✨ קיבלת מטבע 1.')

                        # כפיית יצירת התראה לפעמון (כדי שיקפוץ מיד העדכון למשתמש)
                        from core.utils import send_notification
                        send_notification(
                            recipient=request.user,
                            notification_type='economy',
                            title='קיבלת מטבעות! 🪙',
                            message=f'תודה על הדירוג של {folder_to_edit.staff_member.name}! קיבלת 2 מטבעות.'
                        )

                        messages.success(request, 'התיקייה והדירוג נשמרו, וזכית ב-2 מטבעות! 🪙')
                    else:
                        messages.success(request, 'הדירוג של המרצה עודכן בהצלחה! ✨')
                else:
                    messages.success(request, 'התיקייה עודכנה בהצלחה! 📁')

            if open_this_folder:
                return redirect('course_detail_folder', course_id=course.id, folder_id=open_this_folder)
            return redirect('course_detail', course_id=course.id)

        elif action == 'quick_upload':
            uploaded_files = request.FILES.getlist('file')
            f_id = request.POST.get('folder_id')
            p_folder = None

            if f_id and f_id not in ['root', 'null', 'None']:
                p_folder = get_object_or_404(Folder, id=f_id, course=course)

            from django.core.exceptions import ValidationError
            from core.utils import validate_file_size, validate_file_type
            uploaded_count = 0
            for uploaded_file in uploaded_files:
                try:
                    validate_file_size(uploaded_file)
                    validate_file_type(uploaded_file)
                except ValidationError:
                    continue
                Document.objects.create(
                    course=course,
                    folder=p_folder,
                    title=os.path.splitext(uploaded_file.name)[0],
                    file=uploaded_file,
                    uploaded_by=request.user,
                    staff_member=p_folder.staff_member if p_folder else None,
                    uploader_ip=get_client_ip(request)
                )
                process_transaction(request.user, 1, tx_type='system', description='בונוס על העלאת מסמך')
                uploaded_count += 1
            return JsonResponse({'success': True, 'count': uploaded_count})

    all_folders = Folder.objects.filter(course=course).select_related('staff_member')
    all_documents = Document.objects.filter(course=course).select_related(
        'uploaded_by', 'staff_member'
    ).prefetch_related('likes').order_by('-upload_date')

    context = {
        'course': course,
        'folders': all_folders,
        'documents': all_documents,
        'uni_lecturers': AcademicStaff.objects.filter(university=course.major.university).order_by('name'),
        'target_folder_id': open_this_folder,
    }
    return render(request, 'core/course_detail.html', context)

@login_required
def toggle_favorite_course(request, course_id):
    if request.method == 'POST':
        course = get_object_or_404(Course, id=course_id)
        profile = request.user.profile

        selection, created = UserCourseSelection.objects.get_or_create(
            user=request.user,
            course=course
        )

        if course in profile.favorite_courses.all():
            profile.favorite_courses.remove(course)
            selection.is_starred = False
            is_favorite = False
        else:
            profile.favorite_courses.add(course)
            selection.is_starred = True
            is_favorite = True

        selection.save()
        return JsonResponse({'is_favorite': is_favorite})
    return JsonResponse({'error': 'בקשה לא חוקית'}, status=400)

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

# ==========================================
# 3. Academic staff
# ==========================================

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
            from django.db.models import Avg
            avg = staff.reviews.aggregate(Avg('rating'))['rating__avg']
            staff.average_rating = round(avg, 1)
            staff.save()

            if created:
                if check_daily_limit(request.user, 'add_review', 2):
                    process_transaction(request.user, 1, tx_type='system', description='בונוס על דירוג איש סגל ✨ קיבלת מטבע 1.')

                # מנגנון בונוס האיכות! אם המרצה הגיע ל-10 דירוגים, מי שיצר אותו מקבל 5 מטבעות
            if staff.reviews.count() == 10 and getattr(staff, 'created_by', None):
                process_transaction(
                    user=staff.created_by,
                    amount=5,
                    tx_type='quality_bonus',
                    description=f"בונוס איכות! המרצה שהוספת ({staff.name}) הגיע ל-10 דירוגים 🔥",
                    notify=True,
                    bonus_increases_lifetime=True
                )

            messages.success(request, 'הדירוג עודכן בהצלחה! ✨')
    return redirect('staff_detail', staff_id=staff.id)


@login_required
def add_comment_doc(request, document_id):
    if request.method == "POST":
        text = request.POST.get('comment_text')
        if text:
            document = get_object_or_404(Document, id=document_id)
            comment = DocumentComment.objects.create(
                document=document,
                user=request.user,
                text=text
            )
            # Return JSON instead of redirecting so the frontend can update immediately
            return JsonResponse({
                'status': 'success',
                'user': request.user.username,
                'text': comment.text
            })
    
    return JsonResponse({'status': 'error'}, status=400)
