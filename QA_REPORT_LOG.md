# QA_REPORT_LOG — 2026-04-22 Nightly Audit

## Executive Summary

**Overall Site Health: FAIR — actionable critical and high-severity issues remain.**

The Student Drive platform has materially improved since the previous audit cycle: all five previously-reported
security regressions have been patched and the automated test suite has grown from 42 to 60 passing tests.
However, three new or persistent vulnerabilities warrant immediate attention before the next production push.

### Top 3 Critical Issues Requiring Immediate Attention

1. **[CRITICAL] Unrestricted cross-user document access** — any authenticated user can view or download any
   course-linked file regardless of enrollment.  Exploitable at `/download/<id>/` and `/document/<id>/view/`.
2. **[HIGH] Unvalidated file upload in the private chat room** — `chat_room` stores `local_file` attachments
   directly to the database/storage with no size, MIME-type, or extension check, enabling malware or
   oversized-file uploads.
3. **[HIGH] Broken error-redirect in `download_file`** — the `except` block calls
   `redirect('course_detail', course_id=d.course.id)` unconditionally; if the document has no linked course
   (chat files, personal-drive files) this raises `AttributeError` and returns an unhandled 500.

---

## Audit Table

| Component | Feature Tested | Status | Severity | Issue Description | Suggested Fix |
|-----------|---------------|--------|----------|-------------------|---------------|
| Auth | Registration flow | Pass | — | `allauth` adapter active; email-verified signup works as expected. No issues found. | — |
| Auth | Login / Logout | Pass | — | Session management correct; `SESSION_COOKIE_HTTPONLY=True`, CSRF enforced. | — |
| Auth | Password change | Pass | — | `change_password` uses `PasswordChangeForm` + `update_session_auth_hash`; Google-OAuth users correctly blocked. | — |
| Auth | Google OAuth login | Pass | — | `allauth` social-auth adapter present; OAuth state parameters used. | — |
| Auth | Account deletion | Pass | — | `delete_account` logs the user out before deleting; no orphaned session risk. | — |
| File System | File upload (PDF/PNG/ZIP) | Pass | — | `validate_file_size` and `validate_file_type` enforced at `ShareTargetFinishView.post`. | — |
| File System | File upload — **chat room** | **Fail** | **High** | `chat_room` (`friends_chat.py:248-256`) stores `local_file` with **no** call to `validate_file_size` or `validate_file_type`. Any file type/size is accepted. | Call `validate_file_size(local_file)` and `validate_file_type(local_file)` before `Document.objects.create`; return an error message on `ValidationError`. |
| File System | File upload — external resource | **Fail** | **Medium** | `add_external_resource` (`personal_drive.py:92-118`) stores `file = request.FILES.get('file')` without validation. | Add the same `validate_file_size`/`validate_file_type` guards used in the share-target upload flow. |
| File System | Document download (own file) | Pass | — | Correct counter increment, log creation, and `Content-Disposition` header. | — |
| File System | Document download (cross-user, course-linked) | **Fail** | **Critical** | `_can_user_access_document` (`documents.py:193-205`) grants access to **any** authenticated user for any document with a non-null `course_id`. There is no enrollment or explicit sharing check. | Introduce an enrollment/membership gate: only allow download if `request.user == doc.uploaded_by` **or** the user is a member of the document's course/community. Add explicit sharing model if needed. |
| File System | Document view (cross-user, course-linked) | **Fail** | **Critical** | Same `_can_user_access_document` flaw applies to `document_viewer`. | Same fix as download. |
| File System | Download error path (no course) | **Fail** | **High** | `download_file` catches `Exception` then calls `redirect('course_detail', course_id=d.course.id)` (`documents.py:238-240`). When `d.course` is `None` (chat/personal-drive files) this raises `AttributeError` → unhandled 500. | Replace with `redirect(request.META.get('HTTP_REFERER', 'personal_drive'))` or guard with `if d.course else redirect('personal_drive')`. |
| File System | File deletion (own) | Pass | — | `delete_item_ajax` uses `check_deletion_permission`; ownership enforced. | — |
| File System | AWS S3 integration | Pass | — | `DEFAULT_FILE_STORAGE` uses `storages.backends.s3boto3.S3Boto3Storage` in production; environment credentials loaded via `os.getenv`. | — |
| File System | `ShareTargetView` CSRF exemption | **Fail** | **Medium** | `ShareTargetView` is decorated with `@csrf_exempt` (`documents.py:60`), allowing cross-origin POST requests to stage files in the server's temp storage. | Limit exemption to legitimate OS share-target agents using `Origin` / `Referer` header validation, or restrict to authenticated requests with a custom CSRF token header. |
| Social | Send friend request | Pass | — | Now guarded by `@require_POST`; GET requests return HTTP 405. | — |
| Social | Accept friend request | **Fail** | **Medium** | `accept_friend_request` (`friends_chat.py:118`) is not decorated with `@require_POST`. A crafted `GET /friend/accept/<id>/` link can accept a pending request without user intent. | Add `@require_POST` decorator. |
| Social | Reject friend request | **Fail** | **Medium** | `reject_friend_request` (`friends_chat.py:142`) is not decorated with `@require_POST`. Same CSRF-via-GET exposure as accept. | Add `@require_POST` decorator. |
| Social | Remove friend | **Fail** | **Medium** | `remove_friend` (`friends_chat.py:168`) is not decorated with `@require_POST`. A malicious link can silently remove a friendship. | Add `@require_POST` decorator. |
| Social | Private chat (text message) | Pass | — | Participants-only room access correctly enforced (`get_object_or_404(ChatRoom, …, participants=request.user)`). | — |
| Social | Add comment (XSS) | Pass | — | `add_comment` now calls `escape(comment.text)` (`social.py:166`) before returning JSON. Frontend safe. | — |
| Social | University/Major creation (unauthenticated) | Pass | — | `add_university_ajax` and `add_major_ajax` now check `request.user.is_authenticated` and return HTTP 401 for anonymous requests. | — |
| Social | University/Major creation (authorization level) | **Fail** | **Low** | Any authenticated user (not just staff/admin) can create new University or Major records. No role check beyond `is_authenticated`. | Add `if not request.user.is_staff: return JsonResponse(…, status=403)` or a dedicated permission group check. |
| Social | `load_majors` API exposure | **Fail** | **Low** | `load_majors` (`api.py:36`) returns all majors for a given university ID without requiring authentication. Leaks academic catalogue data publicly. | Add `@login_required` decorator (consistent with all other API endpoints). |
| Social | Cross-user tag mutation | Pass | — | `update_resource_tag` now validates `obj.uploaded_by_id != request.user.id` and returns HTTP 403. | — |
| Auth/Security | Report endpoint method abuse | Pass | — | `report_document` now enforces `@require_POST`; GET returns HTTP 405. | — |
| UI/UX | Dark Mode — CSS variables | Pass | — | `[data-bs-theme="dark"]` block in `base.html` overrides all major design tokens. No critical missing variables found. | — |
| UI/UX | Dark Mode — persistence | **Fail** | **Low** | Theme is read from `user.profile.theme_preference` on initial render (`base.html:8`), but a small JS snippet applies it from `localStorage` before the first paint (`base.html:15-16`). These two sources can diverge if the user changes theme in another tab or browser. | Sync `localStorage` write to the settings-save AJAX response so both sources stay in agreement. |
| UI/UX | Lecturers page — stray character | **Fail** | **Low** | `lecturers_index.html` starts with `={% extends … %}` (visible `=` rendered before template tag). Causes a text artifact at the page top on all browsers. | Remove the leading `=` character from line 1 of `core/templates/core/lecturers_index.html`. |
| UI/UX | Mobile responsiveness | Pass | — | Bootstrap 5 grid and RTL (`dir="rtl"`) applied globally; navbar collapses correctly at `<768 px` breakpoint. | — |
| UI/UX | Tablet responsiveness | Pass | — | Layout validated at 768 px–1024 px; no overflow or broken grids observed in template inspection. | — |
| Automation | n8n / AI agent triggers | N/A | — | Agent view routes are commented out in `urls.py` (`#path('agent/upload/…')`). n8n integration not active in current codebase. | Re-enable and test when integration is restored. |
| Automation | AI document summary | Pass | — | `summarize_document_ai` calls `generate_smart_summary`; access-controlled by `@login_required`. | — |
| Security | SQL injection surface | Pass | — | All queries use Django ORM; no raw SQL or `cursor.execute` paths found. | — |
| Security | Session cookie security | Pass | — | `SESSION_COOKIE_HTTPONLY=True`, `CSRF_COOKIE_HTTPONLY=True`; production enforces `SECURE_SSL_REDIRECT` and HSTS (1 year). | — |
| Security | HSTS configuration | Pass | — | `SECURE_HSTS_SECONDS=31536000`, `INCLUDE_SUBDOMAINS=True`, `PRELOAD=True` in production settings. | — |
| Testing | Automated regression coverage | Pass | — | Test suite: **60 tests, all pass** (up from 42 in previous cycle). | Continue adding tests for cross-user access and chat file upload paths. |

---

## Remediation Priority

| Priority | Ticket | Effort |
|----------|--------|--------|
| P0 — Immediate | Cross-user document view/download (Critical) | Medium |
| P0 — Immediate | Chat-room file upload validation (High) | Low |
| P0 — Immediate | Download error-redirect crash on courseless files (High) | Low |
| P1 — This sprint | Accept/Reject/Remove friend `@require_POST` guards (Medium × 3) | Low |
| P1 — This sprint | `ShareTargetView` CSRF exemption scope (Medium) | Medium |
| P2 — Next sprint | External resource upload validation (Medium) | Low |
| P2 — Next sprint | University/Major creation role-check (Low) | Low |
| P3 — Backlog | `load_majors` auth gate (Low) | Low |
| P3 — Backlog | Dark Mode `localStorage` / DB sync (Low) | Low |
| P3 — Backlog | Lecturers page stray `=` character (Low) | Trivial |
