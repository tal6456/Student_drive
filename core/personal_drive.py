"""
Student personal drive management
=================================
This file manages each user's private storage area in the site.
It lets the student view uploaded files, browse download history,
and manage private external resources.
The code automatically groups files by course and folder, and lets the
user clear history, permanently delete their own content, or add resources.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
# Import the models defined in `models.py`
from .models import Document, DownloadLog, Vote, ExternalResource


@login_required
def personal_drive(request):
    user = request.user
    
    # 1. Fetch all files uploaded by the user, with `select_related` for performance
    uploaded_files_queryset = Document.objects.filter(uploaded_by=user).select_related('course',
                                                                                       'folder').prefetch_related(
        'likes', 'comments').order_by('-upload_date')
    CONTENT_TYPES = ['הרצאות', 'תרגולים', 'מטלות', 'מבחני עבר', 'חומרי עזר נוספים', 'עמית']
    
    processed_uploads = []
    for doc in uploaded_files_queryset:
        # Unique identifier used by the HTML layer
        doc.unique_row_id = f"up_{doc.id}"
        
        # Folder detection logic, matching the download-history behavior
        doc.top_folder_name = "קבצים כלליים"
        if doc.folder:
            current = doc.folder
            while current:
                if current.name in CONTENT_TYPES:
                    doc.top_folder_name = current.name
                    break
                current = getattr(current, 'parent', None)
        
        processed_uploads.append(doc)

    # Sort so Django's `regroup` in HTML behaves correctly
    processed_uploads.sort(key=lambda x: (
        x.course.name if x.course else "ללא קורס",
        x.top_folder_name
    ))

    # 2. Handle download history using the existing behavior
    logs_queryset = DownloadLog.objects.filter(user=user).select_related(
        'document__course',
        'document__folder',
        'document__uploaded_by'
    ).prefetch_related('document__likes', 'document__comments')

    processed_logs = []
    for log in logs_queryset:
        log.unique_row_id = f"dl_{log.id}"
        log.top_folder_name = "קבצים כלליים"
        if log.document and log.document.folder:
            current = log.document.folder
            while current:
                if current.name in CONTENT_TYPES:
                    log.top_folder_name = current.name
                    break
                current = getattr(current, 'parent', None)
        processed_logs.append(log)

    processed_logs.sort(key=lambda x: (
        x.document.course.name if x.document and x.document.course else "ללא קורס",
        x.top_folder_name
    ))

    # External resources and vote history
    external_resources = ExternalResource.objects.filter(user=user).order_by('-created_at')
    voted_files = Vote.objects.filter(user=user).select_related('document').order_by('-created_at')

    context = {
        'uploaded_files': processed_uploads,  # They are now processed and sorted
        'download_logs': processed_logs,
        'voted_files': voted_files,
        'external_resources': external_resources,
    }
    return render(request, 'core/personal_drive.html', context)


# --- External resource helpers ---

@login_required
def add_external_resource(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        link = request.POST.get('link')
        file = request.FILES.get('file')

        if title:
            resource = ExternalResource.objects.create(
                user=request.user,
                title=title,
                link=link,
                file=file
            )
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'id': resource.id,
                    'title': resource.title,
                    'link': resource.link,
                    'file_url': resource.file.url if resource.file else '',
                    'personal_tag': resource.personal_tag,
                    'created_at': resource.created_at.strftime('%d/%m/%Y')
                })

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Missing title or invalid submission.'}, status=400)

    return redirect('personal_drive')


@login_required
def delete_external_resource(request, resource_id):
    resource = get_object_or_404(ExternalResource, id=resource_id, user=request.user)
    resource.delete()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'resource_id': resource_id})
    return redirect('personal_drive')


# --- Original deletion helpers ---

@login_required
def remove_from_history(request, log_id):
    """מסיר את הרישום מההיסטוריה (מהדרייב האישי) בלי למחוק את הקובץ מהאתר"""
    log = get_object_or_404(DownloadLog, id=log_id, user=request.user)
    log.delete()
    return redirect('personal_drive')


@login_required
def delete_my_upload(request, doc_id):
    """מחיקה סופית של קובץ שהמשתמש העלה"""
    doc = get_object_or_404(Document, id=doc_id, uploaded_by=request.user)
    doc.delete()
    return redirect('personal_drive')


@login_required
def update_resource_tag(request):
    if request.method == 'POST':
        res_type = request.POST.get('type')  # 'doc' or 'external'
        res_id = request.POST.get('id')
        new_tag = request.POST.get('tag')

        if res_type == 'doc':
            # Look in regular documents
            obj = get_object_or_404(Document, id=res_id)
        else:
            # Look in external resources
            obj = get_object_or_404(ExternalResource, id=res_id, user=request.user)

        obj.personal_tag = new_tag
        obj.save()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'id': res_id,
                'type': res_type,
                'new_tag': new_tag
            })

    return redirect('personal_drive')
