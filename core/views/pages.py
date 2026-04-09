from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Q

# ייבוא רק של המודלים הנדרשים לכאן
from core.models import Document, Course, UserProfile, Report, Feedback


# ==========================================
# 1. דפי מידע וסטטיים
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
# 2. מערכת, משוב ואנליטיקס
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
# 3. דפי שגיאה מערכתיים
# ==========================================

def error_404(request, exception):
    return render(request, '404.html', status=404)

def error_500(request):
    return render(request, '500.html', status=500)