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
from urllib.parse import quote
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, Http404

# Import the models and helpers needed by this module
from core.models import Document, DownloadLog, Report
from core.ai_utils import generate_smart_summary


@login_required
def download_file(request, document_id):
    d = get_object_or_404(Document, id=document_id)
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

    ext = document.file_extension.replace('.', '').lower()
    file_type = 'other'
    text_content = None

    if ext in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
        file_type = 'image'
    elif ext == 'pdf':
        file_type = 'pdf'
    elif ext in ['doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx']:
        file_type = 'office'
    elif ext == 'txt':
        file_type = 'text'
        try:
            document.file.open('rb')
            raw_data = document.file.read()
            try:
                text_content = raw_data.decode('utf-8')
            except UnicodeDecodeError:
                text_content = raw_data.decode('windows-1255', errors='replace')
        except Exception:
            text_content = "אירעה שגיאה בטעינת תוכן הקובץ."
        finally:
            document.file.close()

    context = {
        'document': document,
        'file_type': file_type,
        'text_content': text_content,
        'absolute_file_url': request.build_absolute_uri(document.file.url)
    }
    return render(request, 'core/document_viewer.html', context)


@login_required
def summarize_document_ai(request, document_id):
    d, p = get_object_or_404(Document, id=document_id), request.user.profile
    s = generate_smart_summary(d)

    if "שגיאה" not in s:
        return JsonResponse({'success': True, 'summary': s, 'new_coins': p.current_balance})

    return JsonResponse({'success': False, 'error': s})


@login_required
def report_document(request, document_id):
    if request.method == 'POST':
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
            if doc.uploaded_by and doc.uploaded_by != request.user:
                doc.uploaded_by.profile.earn_coins(1)

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
            course=original_doc.course
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
