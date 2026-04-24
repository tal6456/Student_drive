"""
Document lifecycle management
=============================

This file handles documents from upload through download and interaction.

It covers:
1. Secure downloads with counters and logs.
2. In-browser document viewing by file type.
3. AI-based summaries.
4. Likes and abuse reports.
5. Personal-drive copy and history management.
"""

import mimetypes
import os
import uuid
from urllib.parse import quote
from urllib.parse import urlencode
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, Http404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.base import File
from django.core.files.storage import default_storage
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

# Import the models and helpers needed by this module
from core.models import Course, Document, DownloadLog, Major, Report
from core.ai_utils import generate_smart_summary
from core.utils import get_client_ip, validate_file_size, validate_file_type, process_transaction, check_daily_limit


def _ensure_session_key(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def _get_staged_shared_files(request):
    return request.session.get('shared_upload_staged_files', [])


def _clear_staged_shared_files(request):
    staged_files = _get_staged_shared_files(request)
    for file_info in staged_files:
        file_path = file_info.get('path')
        if file_path and default_storage.exists(file_path):
            default_storage.delete(file_path)
    request.session.pop('shared_upload_staged_files', None)
    request.session.modified = True


@method_decorator(csrf_exempt, name='dispatch')
class ShareTargetView(View):
    """Handle incoming OS-level shared files and stage them for final upload."""

    def post(self, request, *args, **kwargs):
        files = request.FILES.getlist('shared_files')
        if not files:
            messages.error(request, 'לא התקבלו קבצים לשיתוף.')
            return redirect('home')

        session_key = _ensure_session_key(request)
        _clear_staged_shared_files(request)
        staged_files = []

        for shared_file in files:
            safe_name = os.path.basename(shared_file.name or 'shared-file')
            temp_name = f"shared_uploads/{session_key}/{uuid.uuid4().hex}_{safe_name}"
            stored_path = default_storage.save(temp_name, shared_file)
            staged_files.append({
                'path': stored_path,
                'original_name': safe_name,
                'size': getattr(shared_file, 'size', 0),
                'content_type': getattr(shared_file, 'content_type', '')
            })

        request.session['shared_upload_staged_files'] = staged_files
        request.session.modified = True

        if not request.user.is_authenticated:
            login_path = reverse('account_login')
            finish_path = reverse('share_target_finish')
            query = urlencode({'next': finish_path})
            return redirect(f"{login_path}?{query}")

        return redirect('share_target_finish')


class ShareTargetFinishView(LoginRequiredMixin, View):
    template_name = 'core/share_target_finish.html'
    login_url = '/accounts/login/'

    def get(self, request, *args, **kwargs):
        staged_files = _get_staged_shared_files(request)
        if not staged_files:
            messages.info(request, 'אין כרגע קבצים משותפים שממתינים להעלאה.')
            return redirect('home')

        majors = Major.objects.select_related('university').order_by('university__name', 'name')
        courses = Course.objects.select_related('major__university').order_by('name')
        context = {
            'staged_files': staged_files,
            'majors': majors,
            'courses': courses,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        staged_files = _get_staged_shared_files(request)
        if not staged_files:
            messages.error(request, 'לא נמצאו קבצים להעלאה. נסה לשתף שוב מהאפליקציה.')
            return redirect('home')

        major_id = request.POST.get('major_id')
        course_id = request.POST.get('course_id')
        if not major_id or not course_id:
            messages.error(request, 'יש לבחור קורס לפני סיום ההעלאה.')
            return redirect('share_target_finish')

        course = get_object_or_404(Course, id=course_id)
        if not course.major_id or str(course.major_id) != str(major_id):
            messages.error(request, 'הקורס שנבחר לא שייך לפקולטה שנבחרה.')
            return redirect('share_target_finish')

        uploaded_count = 0

        for file_info in staged_files:
            file_path = file_info.get('path')
            original_name = file_info.get('original_name') or 'shared-file'

            if not file_path or not default_storage.exists(file_path):
                continue

            with default_storage.open(file_path, 'rb') as staged_file:
                django_file = File(staged_file, name=original_name)
                try:
                    validate_file_size(django_file)
                    validate_file_type(django_file)
                except ValidationError:
                    continue

                Document.objects.create(
                    course=course,
                    title=os.path.splitext(original_name)[0],
                    file=django_file,
                    uploaded_by=request.user,
                    uploader_ip=get_client_ip(request)
                )
                # הבונוס המוגן: 5 מטבעות, עד 5 ביום
                if check_daily_limit(request.user, 'document_upload', 5):
                    process_transaction(request.user, 5, 'document_upload', "בונוס על העלאת חומר לימוד 📄", notify=True)
                uploaded_count += 1

            default_storage.delete(file_path)

        request.session.pop('shared_upload_staged_files', None)
        request.session.modified = True

        if uploaded_count:
            messages.success(request, f'{uploaded_count} קבצים הועלו בהצלחה לקורס {course.name}.')
            return redirect('course_detail', course_id=course.id)

        messages.error(request, 'הקבצים לא הועלו. ודא שסוג וגודל הקבצים נתמכים.')
        return redirect('share_target_finish')


TEXT_PREVIEW_EXTENSIONS = {'txt', 'py', 'c', 'cpp', 'cc', 'cxx', 'h', 'hpp', 'hh', 'hxx'}


def _read_document_text(document):
    try:
        document.file.open('rb')
        raw_data = document.file.read()
        try:
            return raw_data.decode('utf-8')
        except UnicodeDecodeError:
            return raw_data.decode('windows-1255', errors='replace')
    except Exception:
        return "אירעה שגיאה בטעינת תוכן הקובץ."
    finally:
        try:
            document.file.close()
        except Exception:
            pass


def _can_user_access_document(user, document):
    if document.uploaded_by_id == user.id:
        return True

    # Course-linked files are treated as shared content.
    if document.course_id:
        return True

    # Community-linked files may exist in future schema/extensions.
    if getattr(document, 'community_id', None):
        return True

    return False


@login_required
def download_file(request, document_id):
    d = get_object_or_404(Document, id=document_id)
    if not _can_user_access_document(request.user, d):
        raise Http404("המסמך המבוקש אינו זמין.")

    d.download_count += 1
    d.save()

    # Record the download in the system log
    DownloadLog.objects.create(user=request.user, document=d)

    if not d.file:
        raise Http404("הקובץ המבוקש לא נמצא בשרת.")

    try:
        file_obj = d.file.open('rb')
        content_type, encoding = mimetypes.guess_type(d.file.name)
        content_type = content_type or 'application/octet-stream'

        response = HttpResponse(file_obj, content_type=content_type)
        safe_filename = quote(d.title.encode('utf-8'))

        file_ext = f".{d.file_extension}" if hasattr(d, 'file_extension') and d.file_extension else ""
        if file_ext and not safe_filename.lower().endswith(file_ext.lower()):
            safe_filename += file_ext

        response['Content-Disposition'] = f"attachment; filename*=UTF-8''{safe_filename}"
        return response

    except Exception as e:
        messages.error(request, f"אירעה שגיאה בהורדת הקובץ: {str(e)}")
        return redirect('course_detail', course_id=d.course.id)


@login_required
def document_viewer(request, document_id):
    document = get_object_or_404(Document, id=document_id)
    if not _can_user_access_document(request.user, document):
        raise Http404("המסמך המבוקש אינו זמין.")

    ext = document.file_extension.replace('.', '').lower()
    file_type = 'other'
    text_content = None

    if ext in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
        file_type = 'image'
    elif ext == 'pdf':
        file_type = 'pdf'
    elif ext in ['doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx']:
        file_type = 'office'
    elif ext in TEXT_PREVIEW_EXTENSIONS:
        file_type = 'text'
        text_content = _read_document_text(document)

    context = {
        'document': document,
        'file_type': file_type,
        'text_content': text_content,
        'absolute_file_url': request.build_absolute_uri(document.file.url),
    }
    return render(request, 'core/document_viewer.html', context)


@login_required
def summarize_document_ai(request, document_id):
    d, p = get_object_or_404(Document, id=document_id), request.user.profile

    # 1. בדיקת יתרה
    if p.current_balance < 2:
        return JsonResponse({'success': False, 'error': 'אין לך מספיק מטבעות (נדרשים 2 מטבעות לסיכום).'})

    # 2. הרצת ה-AI
    s = generate_smart_summary(d)

    if "שגיאה" not in s:
        # 3. גביית תשלום (מינוס 2) רק אם הסיכום הצליח
        process_transaction(request.user, -2, 'ai_summary', f"תשלום על בקשת סיכום למסמך '{d.title}'", notify=False)
        return JsonResponse({'success': True, 'summary': s, 'new_coins': p.current_balance - 2})

    return JsonResponse({'success': False, 'error': s})


@login_required
@require_POST
def report_document(request, document_id):
    d = get_object_or_404(Document, id=document_id)
    Report.objects.create(document=d, user=request.user, reason=request.POST.get('reason'),
                          description=request.POST.get('description', ''))
    messages.success(request, 'הדיווח התקבל וייבדק בהקדם על ידי ההנהלה.')
    return redirect('course_detail', course_id=d.course.id)


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
            # מחקנו את התשלום על כל לייק בודד, ועברנו לבונוס איכות של 10 לייקים
            if doc.total_likes == 10 and doc.uploaded_by:
                process_transaction(
                    user=doc.uploaded_by,
                    amount=10,
                    tx_type='quality_bonus',
                    description=f"בונוס איכות! הקובץ '{doc.title}' שובר שיאים וקיבל 10 לייקים 🔥",
                    notify=True,
                    bonus_increases_lifetime=True
                )

        return JsonResponse({'liked': liked, 'total_likes': doc.total_likes})
    return JsonResponse({'error': 'בקשה לא חוקית'}, status=400)


@login_required
def remove_from_history(request, log_id):
    if request.method == 'POST':
        log = get_object_or_404(DownloadLog, id=log_id, user=request.user)
        log.delete()
    return redirect('personal_drive')


@login_required
def copy_file_to_my_drive(request, document_id):
    original_doc = get_object_or_404(Document, id=document_id)
    already_exists = Document.objects.filter(
        uploaded_by=request.user,
        file=original_doc.file
    ).exists()

    if not already_exists:
        Document.objects.create(
            uploaded_by=request.user,
            title=f"עותק של {original_doc.title}",
            file=original_doc.file,
            course=original_doc.course,
            uploader_ip = get_client_ip(request)
        )
        messages.success(request, f"הקובץ '{original_doc.title}' נוסף לדרייב שלך!")
    else:
        messages.info(request, "הקובץ כבר קיים בדרייב האישי שלך.")

    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def delete_entire_course_folder(request):
    if request.method == 'POST':
        course_name = request.POST.get('course_name')
        
        # Delete all documents uploaded by the user for this course bucket
        if course_name == "ללא קורס":
            Document.objects.filter(uploaded_by=request.user, course__isnull=True).delete()
        else:
            # Match by course name because that is what the HTML `grouper` uses
            Document.objects.filter(uploaded_by=request.user, course__name=course_name).delete()
            
        messages.success(request, f"התיקייה '{course_name}' נמחקה בהצלחה מהדרייב שלך.")
    
    return redirect('personal_drive')

@login_required
def delete_download_history_folder(request):
    if request.method == 'POST':
        course_name = request.POST.get('course_name')
        from core.models import DownloadLog  # Keep the import local and explicit
        
        if course_name == "ללא קורס":
            DownloadLog.objects.filter(user=request.user, document__course__isnull=True).delete()
        else:
            DownloadLog.objects.filter(user=request.user, document__course__name=course_name).delete()
            
        messages.success(request, f"היסטוריית ההורדות של '{course_name}' נמחקה.")
    
    return redirect('personal_drive')
