from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum  # הוספנו את Sum לכאן!
from .models import University, Major, Course, Document
from .forms import DocumentUploadForm, UserRegisterForm


# --- הרשמה ---
def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserRegisterForm()
    return render(request, 'core/register.html', {'form': form})


# --- התנתקות ---
def logout_view(request):
    logout(request)
    return redirect('home')


# --- דף הבית (ניווט וחיפוש קורסים) ---
def home(request):
    search_query = request.GET.get('search')
    uni_id = request.GET.get('university')
    major_id = request.GET.get('major')
    year = request.GET.get('year')

    context = {}

    # מנוע חיפוש מהיר
    if search_query:
        context['courses'] = Course.objects.filter(name__icontains=search_query)
        context['step'] = 'show_courses'
        context['search_query'] = search_query
        return render(request, 'core/home.html', context)

    # שלב 1: בחירת אוניברסיטה
    if not uni_id:
        context['universities'] = University.objects.all()
        context['step'] = 'select_uni'

    # שלב 2: בחירת מקצוע (חוג)
    elif uni_id and not major_id:
        context['majors'] = Major.objects.filter(university_id=uni_id)
        context['step'] = 'select_major'
        context['uni_id'] = uni_id

    # שלב 3: בחירת שנה
    elif major_id and not year:
        context['years'] = [1, 2, 3, 4]
        context['step'] = 'select_year'
        context['major_id'] = major_id
        context['uni_id'] = uni_id

    # שלב 4: הצגת הקורסים של אותה שנה
    else:
        context['courses'] = Course.objects.filter(major_id=major_id, year=year)
        context['step'] = 'show_courses'

    return render(request, 'core/home.html', context)


# --- דף הקורס (רשימת קבצים והעלאה) ---
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    # --- הוספנו את מונה הצפיות ---
    course.view_count += 1
    course.save()

    if request.method == 'POST':
        # רק משתמש מחובר יכול להעלות קבצים
        if not request.user.is_authenticated:
            return redirect('register')

        form = DocumentUploadForm(request.POST, request.FILES)
        # בתוך הפונקציה course_detail, שנה את בלוק השמירה לזה:
        if form.is_valid():
            document = form.save(commit=False)
            document.course = course
            document.uploaded_by = request.user  # <-- השורה הזו שומרת את זהות המעלה
            document.save()
            return redirect('course_detail', course_id=course.id)
    else:
        form = DocumentUploadForm()

    documents = Document.objects.filter(course=course)

    return render(request, 'core/course_detail.html', {
        'course': course,
        'documents': documents,
        'form': form,
        'major_id': course.major.id,
        'year': course.year,
        'uni_id': course.major.university.id
    })


# --- פונקציית הורדה (סופרת הורדות) ---
@login_required
def download_file(request, document_id):
    document = get_object_or_404(Document, id=document_id)

    # שינינו ל-download_count (השם שהגדרנו במודל)
    document.download_count += 1
    document.save()

    return redirect(document.file.url)


# --- לוח בקרה (אנליטיקס) ---
@login_required
def analytics_dashboard(request):
    if not request.user.is_staff:
        return redirect('home')

    # חישוב סך כל ההורדות מכל הקבצים
    total_files = Document.objects.count()
    total_downloads = Document.objects.aggregate(Sum('download_count'))['download_count__sum'] or 0
    total_views = Course.objects.aggregate(Sum('view_count'))['view_count__sum'] or 0

    # קבצים הכי מורדים
    top_downloaded = Document.objects.order_by('-download_count')[:10]

    # קורסים פופולריים (עם ספירת קבצים)
    popular_courses = Course.objects.annotate(num_docs=Count('document')).order_by('-view_count')[:10]

    # פילוח קטגוריות לגרף (מותאם ל-HTML שעשינו)
    files_by_category = Document.objects.values('category').annotate(total=Count('id'))

    context = {
        'total_files': total_files,
        'total_downloads': total_downloads,
        'total_views': total_views,
        'top_downloaded': top_downloaded,
        'popular_courses': popular_courses,
        'files_by_category': files_by_category,
    }
    return render(request, 'core/analytics.html', context)

@login_required
def profile(request):
    # מביא את כל הקבצים שהמשתמש הזה העלה
    user_documents = Document.objects.filter(uploaded_by=request.user).order_by('-upload_date')
    return render(request, 'core/profile.html', {'user_documents': user_documents})