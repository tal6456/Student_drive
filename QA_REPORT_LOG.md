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
    - comment payload reflection + DOM insertion path (XSS)
    - lecturers grid page/backend rendering sanity
- **Security-focused source scans:**
  - SQL injection surface (`raw`, `cursor.execute`, `RawSQL`, `extra`) → no direct raw SQL usage found.
- **C/C++ execution stress-test scope:**
  - No C/C++ code execution service/endpoints found in current repository; stress tests for code execution sandbox are **not applicable** to current codebase state.

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
