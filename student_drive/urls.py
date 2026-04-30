"""
URL routing system
==================

This file wires together the site's main URL endpoints:
1. Core academic navigation and search.
2. Personal drive routes for user-owned content.
3. Community, friends, and chat features.
4. Authentication, privacy, and profile pages.
5. AJAX/API-style helper endpoints.

It also defines error handlers and serves media files during development.
"""

from django.contrib import admin
from django.urls import path, include
# Import the dedicated personal-drive view module
from core import views, personal_drive #agent_views
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
# ==========================================
    # External resources in the drive
    # ==========================================
    path('drive/add-external/', personal_drive.add_external_resource, name='add_external_resource'),
    path('drive/delete-external/<int:resource_id>/', personal_drive.delete_external_resource, name='delete_external_resource'),
    path('drive/update-tag/', personal_drive.update_resource_tag, name='update_resource_tag'),
    # Route kept here alongside the rest of the URL definitions
    path('remove-from-history/<int:log_id>/', views.remove_from_history, name='remove_from_history'),
    # Admin interface
    path('admin/', admin.site.urls),

    # Route that exposes the service worker from the site root
    path('sw.js', TemplateView.as_view(template_name="sw.js", content_type='application/javascript'), name='sw.js'),

    # Signup and authentication system (`allauth`)
    path('accounts/', include('allauth.urls')),

    # Navigation and course pages
    path('', views.home, name='home'),

    # Order matters: the folder-specific path must come before the generic course path
    path('course/<int:course_id>/folder/<int:folder_id>/', views.course_detail, name='course_detail_folder'),
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),

    # Favorite toggle route used from the home page
    path('course/<int:course_id>/toggle_favorite/', views.toggle_favorite_course, name='toggle_favorite_course'),

    path('add-course/', views.CourseCreateView.as_view(), name='add_course'),
    path('course/<int:course_id>/edit/', views.CourseUpdateView.as_view(), name='edit_course'),
    path('course/<int:course_id>/delete/', views.CourseDeleteView.as_view(), name='delete_course'),
    # ==========================================
    # Personal drive routes
    # ==========================================
    path('drive/', personal_drive.personal_drive, name='personal_drive'),
    path('delete-folder/', views.delete_entire_course_folder, name='delete_entire_course_folder'),
    path('delete-download-history/', views.delete_download_history_folder, name='delete_download_history_folder'),

    # ==========================================
    # Community and social features
    # ==========================================
    path('feed/', views.community_feed, name='community_feed'),
    path('u/<str:username>/', views.public_profile, name='public_profile'),
    path('post/<int:post_id>/like/', views.like_post, name='like_post'),
    path('community/<int:community_id>/join/', views.join_community, name='join_community'),
    path('communities/discover/', views.discover_communities, name='discover_communities'),
    path('post/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    # Add a comment to a document
    path('document/<int:document_id>/comment/', views.add_comment_doc, name='add_comment_doc'),

    # Dynamic search and AJAX/API endpoints
    path('search/live/', views.live_search, name='live_search'),
    path('ajax/load-majors/', views.load_majors, name='ajax_load_majors'),

    # File management
    path('download/<int:document_id>/', views.download_file, name='download_file'),
    path('document/<int:document_id>/view/', views.document_viewer, name='document_viewer'),
    path('document/<int:document_id>/like/', views.like_document, name='like_document'),

    # path('files/match/', views.files_tinder, name='files_tinder'),
    # path('files/match/swipe/', views.files_tinder_swipe, name='files_tinder_swipe'),

    path('report/<int:document_id>/', views.report_document, name='report_document'),
    path('upload-shared-file/', views.ShareTargetView.as_view(), name='share_target_upload'),
    path('upload-shared-file/finish/', views.ShareTargetFinishView.as_view(), name='share_target_finish'),

    # Delete objects created by the current user
    path('ajax/delete-item/', views.delete_item_ajax, name='delete_item_ajax'),

    # Add a university or major
    path('ajax/add-university/', views.add_university_ajax, name='add_university_ajax'),
    path('ajax/add-major/', views.add_major_ajax, name='add_major_ajax'),

    # Unread notifications count
    path('ajax/unread-notifications-count/', views.unread_notifications_count, name='unread_notifications_count'),

    # ==========================================
    # Read-Aloud (TTS) Audio Feature
    # ==========================================
    path('document/<int:document_id>/audio/', views.get_document_audio, name='get_document_audio'),
    path('document/<int:document_id>/audio-status/', views.check_audio_status, name='check_audio_status'),
    path('document/<int:document_id>/text/', views.get_document_text, name='get_document_text'),

    # Profile and analytics
    path('profile/', views.profile, name='profile'),
    path('complete-profile/', views.complete_profile, name='complete_profile'),
    path('analytics/', views.analytics_dashboard, name='analytics'),
    path('wallet/', views.wallet_view, name='wallet'),
    path('shop/', views.shop_view, name='shop'),
    path('shop/buy/<int:item_id>/', views.purchase_shop_item, name='purchase_shop_item'),

    # Settings, privacy, and accessibility
    path('settings/', views.settings_view, name='settings'),
    path('settings/password/', views.change_password, name='change_password'),
    path('settings/delete-account/', views.delete_account, name='delete_account'),
    path('accessibility/', views.accessibility_view, name='accessibility'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('terms/', views.terms_view, name='terms'),

    # Academic staff and related pages
    path('lecturers/', views.lecturers_index, name='lecturers_index'),
    path('staff/<int:staff_id>/rate/', views.rate_staff, name='rate_staff'),
    path('staff/<int:staff_id>/', views.staff_detail, name='staff_detail'),
    path('course/<int:course_id>/set_lecturer/', views.set_semester_lecturer, name='set_semester_lecturer'),
    path('feedback/', views.submit_feedback, name='submit_feedback'),
    path('document/<int:document_id>/ai-summary/', views.summarize_document_ai, name='summarize_document_ai'),
    path('donations/', views.donations, name='donations'),

    # Friend system
    path('friend/request/<str:username>/', views.send_friend_request, name='send_friend_request'),
    path('friend/accept/<int:request_id>/', views.accept_friend_request, name='accept_friend_request'),
    path('friend/reject/<int:request_id>/', views.reject_friend_request, name='reject_friend_request'),
    path('my-friends/', views.my_friends, name='my_friends'),
    path('friend/remove/<str:friend_username>/', views.remove_friend, name='remove_friend'),
    path('search-friends/', views.search_users, name='search_users'),

    path('search/', views.global_search, name='global_search'),
    #path('system-architecture-mirror/', views.agent_report, name='agent_report'),

    # ==========================================
    # Notifications
    # ==========================================
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/<int:pk>/resolve/', views.resolve_notification, name='resolve_notification'),

    # ==========================================
    # Personal AI agent
    # ==========================================
    #path('agent/upload/', agent_views.upload_agent_file, name='agent_upload_file'),
    #path('agent/ask/', agent_views.ask_agent_question, name='agent_ask_question'),

       # ==========================================
    # Chat
    # ==========================================
    path('chat/start/<str:username>/', views.get_or_create_chat, name='get_or_create_chat'),
    path('chat/<int:room_id>/', views.chat_room, name='chat_room'),
    path('file/copy/<int:document_id>/', views.copy_file_to_my_drive, name='copy_file_to_my_drive'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'core.views.error_404'
handler500 = 'core.views.error_500'
