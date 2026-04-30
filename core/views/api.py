"""
מה המטרה של הקובץ הזה
----------------------
קובץ ה-API משמש כצינור להעברת נתונים מהירה בין הלקוח (Client) לשרת. 
הוא מאפשר לבצע פעולות "מאחורי הקלעים" ללא צורך ברענון הדף כולו.

הקובץ מטפל ב:
1. טעינה דינמית (Dynamic Loading): שליפת מסלולי לימוד (Majors) לפי האוניברסיטה שנבחרה.
2. נירמול נתונים (Normalization): מנגנון חכם למניעת כפילויות של מוסדות לימוד (למשל: "טכניון" ו-"הטכניון").
3. יצירת נתונים מהירה (AJAX Create): הוספת אוניברסיטאות ומסלולים ישירות מתוך טפסי הרישום.
4. מחיקה גמישה (Generic Delete): פונקציה מאוחדת למחיקת מסמכים, תיקיות, פוסטים ותגובות 
   תוך בדיקת הרשאות קפדנית (מניעת מחיקה של תוכן על ידי מי שאינו הבעלים).
"""


import json
import re
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_http_methods
from django.http import JsonResponse

from core.models import University, Major, Document, Folder, Post, Comment, DocumentAudio



def normalize_string_for_comparison(text):
    if not text:
        return ""
    text = text.strip().lower()
    text = re.sub(r'[-_]+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text


def load_majors(request):
    university_id = request.GET.get('university')
    if university_id:
        majors = Major.objects.filter(university_id=university_id).order_by('name')
        return JsonResponse(list(majors.values('id', 'name')), safe=False)
    return JsonResponse([])


@require_POST
def add_university_ajax(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)

    try:
        data = json.loads(request.body)
        new_name = data.get('name', '').strip()

        if not new_name:
            return JsonResponse({'success': False, 'error': 'שם המוסד לא יכול להיות ריק.'})

        normalized_new_name = normalize_string_for_comparison(new_name)

        for uni in University.objects.all():
            if normalize_string_for_comparison(uni.name) == normalized_new_name:
                return JsonResponse({
                    'success': False,
                    'error': f'מוסד זה כבר קיים במערכת בשם "{uni.name}". אנא בחר אותו מהרשימה.'
                })

        new_uni = University.objects.create(name=new_name)
        return JsonResponse({'success': True, 'id': new_uni.id, 'name': new_uni.name})

    except Exception as e:
        return JsonResponse({'success': False, 'error': 'אירעה שגיאה בשרת. נסה שוב.'})


@require_POST
def add_major_ajax(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)

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

        for major in Major.objects.filter(university=university):
            if normalize_string_for_comparison(major.name) == normalized_new_name:
                return JsonResponse({
                    'success': False,
                    'error': f'המסלול כבר קיים במוסד זה בשם "{major.name}".'
                })

        new_major = Major.objects.create(name=new_name, university=university)
        return JsonResponse({'success': True, 'id': new_major.id, 'name': new_major.name})

    except Exception as e:
        return JsonResponse({'success': False, 'error': 'אירעה שגיאה בשרת. נסה שוב.'})


@login_required
@require_POST
def delete_item_ajax(request):
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            item_type = data.get('type')
            item_id = data.get('id')
        else:
            item_type = request.POST.get('type')
            item_id = request.POST.get('id')

        if not item_type or not item_id:
            return JsonResponse({'success': False, 'error': 'חסרים נתונים למחיקה.'})

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

        from core.utils import check_deletion_permission
        is_allowed, error_msg = check_deletion_permission(request.user, obj, item_type)

        if is_allowed:
            obj.delete()
            return JsonResponse({'success': True, 'message': 'הפריט נמחק בהצלחה.'})
        else:
            return JsonResponse({'success': False, 'error': error_msg})

    except Exception as e:
        return JsonResponse({'success': False, 'error': f'אירעה שגיאה בשרת: {str(e)}'})


@login_required
def unread_notifications_count(request):
    """
    מחזיר את מספר ההתראות שלא נקראו.
    עבור אדמינים: בודק גם אם יש דיווח זכויות יוצרים פתוח שדורש Pop-up.
    """
    from core.models import Notification, Report

    # 1. ספירת התראות רגילה לכל משתמש
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    data = {'unread_count': count}

    # 2. בדיקה מיוחדת לאדמינים (צוות האתר)
    if request.user.is_staff:
        # מחפשים את הדיווח האחרון על זכויות יוצרים שטרם טופל
        urgent_report = Report.objects.filter(reason='copyright', is_resolved=False).order_by('-created_at').first()

        if urgent_report:
            data['has_urgent_alert'] = True
            data['urgent_message'] = f"התקבל דיווח על הפרת זכויות יוצרים בקובץ: {urgent_report.document.title}"
            data['alert_id'] = urgent_report.id
            data['alert_link'] = f"/admin/core/report/{urgent_report.id}/change/"

    return JsonResponse(data)
# ==========================================
# Read-Aloud Audio Feature (TTS)
# ==========================================

@login_required
@require_http_methods(['GET', 'POST'])
def get_document_audio(request, document_id):
    """
    Retrieve the audio file for a document if it exists,
    or trigger generation if not yet created.

    GET ?lang=he  → gTTS Hebrew MP3 (stored separately)
    GET           → pyttsx3 English WAV (stored in DocumentAudio model)
    """
    try:
        document = get_object_or_404(Document, id=document_id)

        has_access = (
            document.uploaded_by == request.user or
            document.downloadlog_set.filter(user=request.user).exists()
        )
        if not has_access and not request.user.is_staff:
            return JsonResponse({'success': False, 'error': 'Access denied'}, status=403)

        lang = request.GET.get('lang', 'en')

        # ── Hebrew branch (gTTS, stored outside DocumentAudio model) ──────────
        if lang == 'he':
            from core.tts_utils import extract_text_from_file, generate_hebrew_audio_from_text
            from django.core.files.base import ContentFile
            from django.core.files.storage import default_storage

            he_path = f'audio_files/audio_{document.id}_he.mp3'

            if default_storage.exists(he_path):
                return JsonResponse({
                    'success': True,
                    'audio_url': default_storage.url(he_path),
                    'status': 'ready',
                })

            # Generate
            ext = document.file_extension.lower()
            text = extract_text_from_file(document.file, ext)
            if not text:
                return JsonResponse({'success': False, 'status': 'failed',
                                     'message': 'Could not extract text.'})

            audio_bytes = generate_hebrew_audio_from_text(text)
            if not audio_bytes:
                return JsonResponse({'success': False, 'status': 'failed',
                                     'message': 'Hebrew audio generation failed.'})

            default_storage.save(he_path, ContentFile(audio_bytes))
            return JsonResponse({
                'success': True,
                'audio_url': default_storage.url(he_path),
                'status': 'ready',
            })

        # ── English branch (pyttsx3, DocumentAudio model) ─────────────────────
        if request.method == 'POST':
            from core.tasks import generate_document_audio_task
            from core.tts_utils import extract_text_from_file, generate_audio_from_text
            from django.core.files.base import ContentFile
            import os

            audio_obj, created = DocumentAudio.objects.get_or_create(document=document)

            try:
                if not audio_obj.is_generated:
                    ext = document.file_extension.lower()
                    text = extract_text_from_file(document.file, ext)
                    if text:
                        print(f"[API] Generating audio synchronously for doc {document_id}...")
                        audio_bytes = generate_audio_from_text(text, language='en')
                        if audio_bytes:
                            filename = f"audio_{document.id}_{os.urandom(4).hex()}.mp3"
                            audio_obj.audio_file.save(filename, ContentFile(audio_bytes), save=False)
                            audio_obj.text_used = text[:500]
                            audio_obj.is_generated = True
                            audio_obj.save()
                            return JsonResponse({'success': True, 'status': 'ready',
                                                 'audio_url': audio_obj.audio_file.url})
            except Exception as sync_error:
                print(f"[API] Sync generation failed: {sync_error}, falling back to Celery...")

            generate_document_audio_task.delay(document_id)
            return JsonResponse({'success': True, 'status': 'generating',
                                 'message': 'Audio generation started. Please wait...'})

        # GET English
        from core.tts_utils import extract_text_from_file, generate_audio_from_text
        from django.core.files.base import ContentFile
        import os

        def _run_sync_generation(audio_obj):
            try:
                ext = document.file_extension.lower()
                text = extract_text_from_file(document.file, ext)
                if not text:
                    return False
                audio_bytes = generate_audio_from_text(text, language='en')
                if not audio_bytes:
                    return False
                filename = f"audio_{document.id}_{os.urandom(4).hex()}.wav"
                audio_obj.audio_file.save(filename, ContentFile(audio_bytes), save=False)
                audio_obj.text_used = text[:500]
                audio_obj.is_generated = True
                audio_obj.save()
                return True
            except Exception as e:
                import traceback
                print(f"❌ [TTS] Generation error for doc {document_id}: {e}")
                traceback.print_exc()
                return False

        try:
            audio = DocumentAudio.objects.get(document=document)
            if audio.is_generated and audio.audio_file:
                return JsonResponse({'success': True, 'audio_url': audio.audio_file.url, 'status': 'ready'})
            else:
                if _run_sync_generation(audio):
                    return JsonResponse({'success': True, 'audio_url': audio.audio_file.url, 'status': 'ready'})
                return JsonResponse({'success': False, 'status': 'failed',
                                     'message': 'Audio generation failed. Please try again.'})
        except DocumentAudio.DoesNotExist:
            audio_obj = DocumentAudio.objects.create(document=document)
            if _run_sync_generation(audio_obj):
                return JsonResponse({'success': True, 'audio_url': audio_obj.audio_file.url, 'status': 'ready'})
            return JsonResponse({'success': False, 'status': 'failed',
                                 'message': 'Audio generation failed. File type may not be supported.'})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(['GET'])
def check_audio_status(request, document_id):
    """
    Check if audio has been generated for a document.
    Useful for polling after triggering generation.
    """
    try:
        document = get_object_or_404(Document, id=document_id)
        
        try:
            audio = DocumentAudio.objects.get(document=document)
            audio_url = None
            
            # Safely get audio URL
            if audio.is_generated and audio.audio_file:
                try:
                    audio_url = audio.audio_file.url
                    return JsonResponse({
                        'success': True,
                        'is_generated': True,
                        'audio_url': audio_url,
                        'status': 'ready'
                    })
                except Exception as file_error:
                    print(f"Error getting audio file URL: {file_error}")
            
            # Not ready — just report status (main generation happens in get_document_audio)
            return JsonResponse({
                'success': False,
                'is_generated': False,
                'audio_url': None,
                'status': 'generating'
            })
        except DocumentAudio.DoesNotExist:
            return JsonResponse({
                'success': False,
                'status': 'not_started',
                'message': 'Audio not yet generated'
            })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse(
            {'success': False, 'error': str(e)},
            status=500
        )


@login_required
@require_http_methods(['GET'])
def get_document_text(request, document_id):
    """
    Return the plain-text content of a document so the browser
    can feed it to the Web Speech API for Hebrew TTS.
    """
    try:
        document = get_object_or_404(Document, id=document_id)

        # Access check
        has_access = (
            document.uploaded_by == request.user or
            document.downloadlog_set.filter(user=request.user).exists()
        )
        if not has_access and not request.user.is_staff:
            return JsonResponse({'success': False, 'error': 'Access denied'}, status=403)

        # Prefer already-extracted file_content, otherwise extract now
        text = document.file_content or ''
        if not text and document.file:
            from core.tts_utils import extract_text_from_file
            text = extract_text_from_file(document.file, document.file_extension.lower())

        if not text:
            return JsonResponse({'success': False, 'error': 'No text could be extracted from this file.'}, status=422)

        return JsonResponse({'success': True, 'text': text[:8000]})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
