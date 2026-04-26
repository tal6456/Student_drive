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
from django.db.models import Q, Case, When, Value, IntegerField, Count, F
from django.utils import timezone

# Import the models and helpers needed by this module
from core.models import Course, Document, DownloadLog, Major, Report, Friendship, UserCourseSelection, Vote
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


def _get_friend_ids(user):
    relations = Friendship.objects.filter(
        Q(user_from=user) | Q(user_to=user),
        status='accepted'
    ).select_related('user_from', 'user_to')
    friend_ids = []
    for rel in relations:
        friend_ids.append(rel.user_to_id if rel.user_from_id == user.id else rel.user_from_id)
    return friend_ids


def _file_discovery_queryset(user):
    profile = user.profile
    favorite_course_ids = list(profile.favorite_courses.values_list('id', flat=True))
    favorite_major_ids = list(
        Course.objects.filter(id__in=favorite_course_ids).values_list('major_id', flat=True).distinct()
    )
    favorite_university_ids = list(
        Course.objects.filter(id__in=favorite_course_ids).values_list('major__university_id', flat=True).distinct()
    )
    voted_ids = list(Vote.objects.filter(user=user).values_list('document_id', flat=True))
    voted_course_ids = list(
        Vote.objects.filter(user=user, document__course_id__isnull=False)
        .values_list('document__course_id', flat=True)
        .distinct()
    )

    # Relevant universe: favorites, same faculty (major), and personal drive files.
    discovery_filter = Q(uploaded_by=user) | Q(course_id__in=favorite_course_ids)

    major_ids = [profile.major_id] if profile.major_id else favorite_major_ids
    university_ids = [profile.university_id] if profile.university_id else favorite_university_ids

    if major_ids:
        discovery_filter |= Q(course__major_id__in=major_ids)
    elif university_ids:
        discovery_filter |= Q(course__major__university_id__in=university_ids)

    return (
        Document.objects
        .select_related('course__major__university', 'uploaded_by')
        .prefetch_related('likes')
        .filter(discovery_filter)
        .exclude(id__in=voted_ids)
        .exclude(course_id__in=voted_course_ids)
        .exclude(file='')
    )


def _rank_discovery_queryset(user, queryset):
    profile = user.profile
    favorite_course_ids = list(profile.favorite_courses.values_list('id', flat=True))
    favorite_major_ids = list(
        Course.objects.filter(id__in=favorite_course_ids).values_list('major_id', flat=True).distinct()
    )
    favorite_university_ids = list(
        Course.objects.filter(id__in=favorite_course_ids).values_list('major__university_id', flat=True).distinct()
    )
    major_ids = [profile.major_id] if profile.major_id else favorite_major_ids
    university_ids = [profile.university_id] if profile.university_id else favorite_university_ids

    return queryset.annotate(
        likes_count=Count('likes', distinct=True),
        comments_count=Count('comments', distinct=True),
        relevance_tier=Case(
            # 1) Favorite courses first
            When(course_id__in=favorite_course_ids, then=Value(1)),
            # 2) Faculty files next (same major)
            When(course__major_id__in=major_ids, then=Value(2)),
            # 3) Personal drive after faculty
            When(uploaded_by=user, then=Value(3)),
            # 4) Fallback (for users without major set, same university docs)
            When(course__major__university_id__in=university_ids, then=Value(4)),
            default=Value(5),
            output_field=IntegerField(),
        ),
        popularity_score=(F('likes_count') * Value(3)) + (F('comments_count') * Value(4)) + F('download_count')
    ).order_by('relevance_tier', '-popularity_score', '-upload_date')


def _build_tips(user, document):
    profile = user.profile
    tips = []
    if document.uploaded_by_id == user.id:
        tips.append('הקובץ כבר נמצא בדרייב האישי שלך - אולי הזמן לעדכן או לשתף אותו לחברים.')

    if document.uploaded_by_id in _get_friend_ids(user):
        tips.append('הקובץ הועלה על ידי חבר/ה שלך - שווה לשאול אותו/ה איך הכי טוב להשתמש בו.')

    if document.course_id and profile.favorite_courses.filter(id=document.course_id).exists():
        tips.append('זה קורס מועדף שלך - תן עדיפות לקבצים עם יותר לייקים לקראת מבחן.')

    if document.course_id and UserCourseSelection.objects.filter(user=user, course_id=document.course_id).exists():
        tips.append('הקורס מסומן אצלך בלמידה פעילה - שמור את הקובץ כבר עכשיו לדרייב.')

    if profile.major_id and document.course and document.course.major_id == profile.major_id:
        tips.append('הקובץ מתוך הפקולטה שלך - סיכוי גבוה שהוא רלוונטי לסמסטר הנוכחי.')

    if profile.university_id and document.course and document.course.major and document.course.major.university_id == profile.university_id:
        tips.append('הקובץ מאותה אוניברסיטה שלך - מתאים לרוב לסגנון מבחנים ולחומרי קורס מקומיים.')

    if not tips:
        tips.append('טיפ: החלק ימינה לקובץ שימושי ולהוסיף אותו מיד לדרייב שלך.')
    return tips[:2]


def _build_reasons(user, document):
    profile = user.profile
    reasons = []

    if document.course_id and profile.favorite_courses.filter(id=document.course_id).exists():
        reasons.append('קורס מועדף')

    if document.course_id and UserCourseSelection.objects.filter(user=user, course_id=document.course_id).exists():
        reasons.append('בלמידה פעילה')

    if profile.major_id and document.course and document.course.major_id == profile.major_id:
        reasons.append('אותה פקולטה')

    if profile.university_id and document.course and document.course.major and document.course.major.university_id == profile.university_id:
        reasons.append('אותה אוניברסיטה')

    if document.uploaded_by_id in _get_friend_ids(user):
        reasons.append('הועלה על ידי חבר')

    if getattr(document, 'likes_count', document.total_likes) >= 5:
        reasons.append('הרבה לייקים')

    if getattr(document, 'comments_count', document.comments.count()) >= 2:
        reasons.append('הרבה תגובות')

    if not reasons:
        reasons.append('התאמה כללית לפרופיל')

    return reasons[:3]


def _serialize_discovery_card(user, document):
    course_name = document.course.name if document.course else 'ללא קורס'
    university_name = (
        document.course.major.university.name
        if document.course and document.course.major and document.course.major.university
        else 'לא צוינה אוניברסיטה'
    )
    uploader = document.uploaded_by.username if document.uploaded_by else 'משתמש לא ידוע'
    extension = (document.file_extension or '').replace('.', '').lower()
    file_url = document.file.url if document.file else ''

    if extension in {'jpg', 'jpeg', 'png', 'webp', 'gif'}:
        preview_type = 'image'
    elif extension == 'pdf':
        preview_type = 'pdf'
    elif extension in TEXT_PREVIEW_EXTENSIONS:
        preview_type = 'text'
    else:
        preview_type = 'file'

    text_preview = (document.file_content or '').strip()[:260]
    if text_preview and len(document.file_content or '') > 260:
        text_preview += '...'

    return {
        'id': document.id,
        'title': document.title,
        'course_name': course_name,
        'university_name': university_name,
        'uploader': uploader,
        'likes': document.total_likes,
        'comments': getattr(document, 'comments_count', document.comments.count()),
        'downloads': document.download_count,
        'uploaded_at': timezone.localtime(document.upload_date).strftime('%d/%m/%Y'),
        'preview_type': preview_type,
        'file_url': file_url,
        'file_extension': extension or 'file',
        'text_preview': text_preview,
        'tips': _build_tips(user, document),
        'reasons': _build_reasons(user, document),
        'view_url': reverse('document_viewer', args=[document.id]),
        'copy_url': reverse('copy_file_to_my_drive', args=[document.id]),
    }


@login_required
def files_tinder(request):
    ranked_qs = _rank_discovery_queryset(request.user, _file_discovery_queryset(request.user))
    first_document = ranked_qs.first()
    first_card = _serialize_discovery_card(request.user, first_document) if first_document else None

    context = {
        'first_card': first_card,
        'remaining_count': ranked_qs.count(),
    }
    return render(request, 'core/files_tinder.html', context)


@login_required
@require_POST
def files_tinder_swipe(request):
    document_id = request.POST.get('document_id')
    action = request.POST.get('action')

    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if action not in {'like', 'dislike'}:
        if is_ajax:
            return JsonResponse({'success': False, 'error': 'פעולה לא חוקית.'}, status=400)
        messages.error(request, 'פעולה לא חוקית.')
        return redirect('files_tinder')

    try:
        document_id = int(document_id)
    except (TypeError, ValueError):
        if is_ajax:
            return JsonResponse({'success': False, 'error': 'מסמך לא תקין.'}, status=400)
        messages.error(request, 'מסמך לא תקין.')
        return redirect('files_tinder')

    document = get_object_or_404(Document, id=document_id)

    candidate_exists = _file_discovery_queryset(request.user).filter(id=document.id).exists() or Vote.objects.filter(
        user=request.user, document=document
    ).exists()
    if not candidate_exists:
        if is_ajax:
            return JsonResponse({'success': False, 'error': 'אין הרשאה לפעולה על המסמך הזה.'}, status=403)
        messages.error(request, 'אין הרשאה לפעולה על המסמך הזה.')
        return redirect('files_tinder')

    vote_value = 1 if action == 'like' else -1
    Vote.objects.update_or_create(
        user=request.user,
        document=document,
        defaults={'value': vote_value}
    )

    if action == 'like':
        document.likes.add(request.user)
    else:
        document.likes.remove(request.user)

    next_document = _rank_discovery_queryset(request.user, _file_discovery_queryset(request.user)).first()
    next_card = _serialize_discovery_card(request.user, next_document) if next_document else None

    if not is_ajax:
        return redirect('files_tinder')

    return JsonResponse({
        'success': True,
        'next_card': next_card,
        'remaining_count': _file_discovery_queryset(request.user).count(),
    })


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

        # מחזירים את הזיהוי החכם של סוג הקובץ
        content_type, encoding = mimetypes.guess_type(d.file.name)
        content_type = content_type or 'application/octet-stream'

        response = HttpResponse(file_obj, content_type=content_type)
        safe_filename = quote(d.title.encode('utf-8'))

        file_ext = f".{d.file_extension}" if hasattr(d, 'file_extension') and d.file_extension else ""
        if file_ext and not safe_filename.lower().endswith(file_ext.lower()):
            safe_filename += file_ext

        # שינוי קריטי עבור אפל (אייפד/אייפון):
        # שינינו את 'attachment' (שמכריח הורדה עיוורת) ל-'inline' (שמאפשר הצגה בדפדפן אם נתמך).
        # ככה באייפד ייפתח PDF בלשונית חדשה, ומשם יוכלו לשתף לכל אפליקציה!
        response['Content-Disposition'] = f"inline; filename*=UTF-8''{safe_filename}"
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
def like_document(request, document_id):
    if request.method == 'POST':
        doc = get_object_or_404(Document, id=document_id)
        if request.user in doc.likes.all():
            doc.likes.remove(request.user)
            liked = False
        else:
            doc.likes.add(request.user)
            liked = True

            # מעבר למודל "איכות על פני כמות": בונוס על הגעה ל-5 לייקים בדיוק
            if doc.total_likes == 5 and doc.uploaded_by:
                process_transaction(
                    user=doc.uploaded_by,
                    amount=5,
                    tx_type='quality_bonus',
                    description=f"בונוס איכות! הקובץ '{doc.title}' הגיע ל-5 לייקים והרווחת 5 מטבעות! 🔥",
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

    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if not already_exists:
        Document.objects.create(
            uploaded_by=request.user,
            title=f"עותק של {original_doc.title}",
            file=original_doc.file,
            course=original_doc.course,
            uploader_ip = get_client_ip(request)
        )
        message = f"הקובץ '{original_doc.title}' נוסף לדרייב שלך!"
        if not is_ajax:
            messages.success(request, message)
        if is_ajax:
            return JsonResponse({'success': True, 'message': message})
    else:
        message = "הקובץ כבר קיים בדרייב האישי שלך."
        if not is_ajax:
            messages.info(request, message)
        if is_ajax:
            return JsonResponse({'success': True, 'message': message, 'already_existed': True})

    if is_ajax:
        return JsonResponse({'success': True, 'message': message})
    
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
