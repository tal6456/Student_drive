# QA_REPORT_LOG

## 1) Test Coverage
- **Feature discovery scope reviewed:**
  - Routing: `student_drive/urls.py`
  - Data model surface: `core/models.py`
  - View layer: `core/views/{academic,documents,social,friends_chat,accounts,api,pages}.py`
  - Personal drive flows: `core/personal_drive.py`
- **Dynamic checks executed:**
  - Baseline automated suite: `python manage.py test` (**42/42 passed**)
  - Manual destructive/security checks via Django test client:
    - report endpoint method abuse
    - anonymous AJAX creation attempts
    - cross-user data access (viewer/download/tag updates)
    - GET-based state changes (friend request)
    - comment payload reflection + DOM     try:
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
        return JsonResponse({'success': False, 'error': 'אירעה שגיאה בשרת. נסה שוב.'})        try:
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
            return JsonResponse({'success': False, 'error': 'אירעה שגיאה בשרת. נסה שוב.'})insertion path (XSS)
    - lecturers grid page/backend rendering sanity
- **Security-focused source scans:**
  - SQL injection surface (`raw`, `cursor.execute`, `RawSQL`, `extra`) → no direct raw SQL usage found.
- **C/C++ execution stress-test scope:**
  - No C/C++ code execution service/endpoints found in current repository; stress tests for code execution sandbox are **not applicable** to current codebase stat  def _can_user_access_document(user, document):
      if document.uploaded_by_id == user.id:
          return True
  
      # Course-linked files are treated as shared content.
      if document.course_id:
          return True
  
      # Community-linked files may exist in future schema/extensions.
      if getattr(document, 'community_id', None):
          return True
  
      return False      def _can_user_access_document(user, document):
          if document.uploaded_by_id == user.id:
              return True
      
          # Course-linked files are treated as shared content.
          if document.course_id:
              return True
      
          # Community-linked files may exist in future schema/extensions.
          if getattr(document, 'community_id', None):
              return True
      
          return False          @login_required
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
                  return redirect('course_detail', course_id=d.course.id)                  @login_required
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
                      return render(request, 'core/document_viewer.html', context)                      @login_required
                      def update_resource_tag(request):
                          if request.method == 'POST':
                              res_type = request.POST.get('type')  # 'doc' or 'external'
                              res_id = request.POST.get('id')
                              new_tag = request.POST.get('tag')
                      
                              if res_type == 'doc':
                                  # Look in regular documents
                                  obj = get_object_or_404(Document, id=res_id)
                                  if obj.uploaded_by_id != request.user.id:
                                      return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
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
                      
                          return redirect('personal_drive')e.

## 2) Success Log
- ORM-based queries are consistently used (no direct SQL execution paths detected).
- Core application test suite currently passes end-to-end (`42` tests).
- Lecturers grid page renders with backend data and HTTP 200 (`/lecturers/`).
- File validators exist for size/type checks in upload lifecycle (`validate_file_size`, `validate_file_type`).

## 3) Error Log

### 3.1 Crash on non-POST report endpoint
- **Location:** `core/views/documents.py:110-117`
- **Severity:** **High**
- **What fails:** `GET /report/<document_id>/` raises `UnboundLocalError` (500) because `d` is referenced outside POST block.
- **Repro steps:**
  1. Login as any user.
  2. Request `GET /report/<valid_document_id>/`.
  3. Observe HTTP 500 (`UnboundLocalError: cannot access local variable 'd'`).

### 3.2 Broken Access Control: anonymous creation of academic entities
- **Location:** `core/views/api.py:44-67`, `core/views/api.py:69-97`
- **Severity:** **High**
- **What fails:** `add_university_ajax` and `add_major_ajax` are POST-only but not auth-protected; anonymous users can create data.
- **Repro steps:**
  1. As unauthenticated client, POST JSON to `/ajax/add-university/` with a valid `name`.
  2. Observe HTTP 200 with `{ "success": true, ... }` and new DB row created.

### 3.3 Broken Access Control: cross-user document metadata mutation
- **Location:** `core/personal_drive.py:150-164`
- **Severity:** **High**
- **What fails:** `update_resource_tag` allows updating tags on `Document` by ID without checking ownership.
- **Repro steps:**
  1. User A uploads a document.
  2. User B sends POST `/drive/update-tag/` with `type=doc&id=<A_doc_id>&tag=important`.
  3. Observe redirect success and User A’s document tag changed.

### 3.4 Broken Access Control: cross-user access to non-course/private documents
- **Location:** `core/views/documents.py:30-55`, `core/views/documents.py:62-95`
- **Severity:** **Critical**
- **What fails:** Any authenticated user can view/download any document by ID (including course-less/chat-style files), with no ownership or membership check.
- **Repro steps:**
  1. User A creates a document with `course=None`.
  2. User B requests `/document/<id>/view/` and `/download/<id>/`.
  3. Observe HTTP 200 for both endpoints.

### 3.5 CSRF-prone state change via GET
- **Location:** `core/views/friends_chat.py:86-113`
- **Severity:** **Medium**
- **What fails:** `send_friend_request` performs a state-changing action without method restriction (accepts GET).
- **Repro steps:**
  1. Login as User B.
  2. Trigger `GET /friend/request/<userA_username>/`.
  3. Observe pending friendship created.

### 3.6 Stored XSS vector in comment rendering path
- **Location:**
  - API response source: `core/views/social.py:152-170`
  - Unsafe DOM insertion: `core/templates/core/base.html:1277-1292`
  - Similar unsafe insertion paths: `core/templates/core/course_detail.html:1034-1050`, `core/templates/core/personal_drive.html:439-453`
- **Severity:** **High**
- **What fails:** Comment text is returned unsanitized and inserted using `insertAdjacentHTML` template strings.
- **Repro steps:**
  1. Submit comment text payload like `<img src=x onerror=alert(1)>`.
  2. API returns raw payload in JSON `text` field.
  3. Frontend inserts payload into HTML via `insertAdjacentHTML`, enabling script execution context.

### 3.7 UI integration defect on grid dashboard page
- **Location:** `core/templates/core/lecturers_index.html:1`
- **Severity:** **Low**
- **What fails:** Stray leading `=` is rendered at page start (visual artifact on grid page).
- **Repro steps:**
  1. Open `/lecturers/`.
  2. Inspect top of rendered HTML/page; leading `=` appears before template content.

## 4) Security Recommendations
1. **Enforce object-level authorization** on document view/download/tagging endpoints (owner, explicit sharing, or course/community membership checks).
2. **Protect mutating API endpoints** (`add_university_ajax`, `add_major_ajax`) with `@login_required` + role-based authorization (moderator/admin).
3. **Enforce HTTP method semantics** (`@require_POST`) for all state-changing actions (friend requests, etc.).
4. **Fix report endpoint control flow**: initialize `d` before branching or return early for non-POST methods to avoid 500s.
5. **Eliminate XSS sinks**:
   - escape/sanitize user-generated text before DOM insertion;
   - avoid `insertAdjacentHTML` for untrusted content;
   - use text nodes / safe templating.
6. **Add regression tests** for: cross-user document access, unauthorized tag updates, anonymous academic object creation, and report endpoint method misuse.
