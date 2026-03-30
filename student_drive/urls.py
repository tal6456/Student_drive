from django.contrib import admin
from django.urls import path, include
# הוספתי כאן את personal_drive לייבוא
from core import views, personal_drive #agent_views
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
# ==========================================
    # משאבים חיצוניים בדרייב
    # ==========================================
    path('drive/add-external/', personal_drive.add_external_resource, name='add_external_resource'),
    path('drive/delete-external/<int:resource_id>/', personal_drive.delete_external_resource, name='delete_external_resource'),
    path('drive/update-tag/', personal_drive.update_resource_tag, name='update_resource_tag'),
    # בתוך קובץ urls.py
    path('remove-from-history/<int:log_id>/', views.remove_from_history, name='remove_from_history'),
    # ממשק ניהול
    path('admin/', admin.site.urls),

    # השורה שמוסיפה את ה-Service Worker לכתובת הראשית:
    path('sw.js', TemplateView.as_view(template_name="sw.js", content_type='application/javascript'), name='sw.js'),

    # מערכת ההרשמה והתחברות (Allauth)
    path('accounts/', include('allauth.urls')),

    # דפי ניווט וקורסים
    # דפי ניווט וקורסים
    path('', views.home, name='home'),

    # שים לב לסדר: קודם הנתיב עם התיקייה, אחר כך הקורס הכללי
    path('course/<int:course_id>/folder/<int:folder_id>/', views.course_detail, name='course_detail_folder'),
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),

    # הנתיב שהיה חסר לך וגרם לשגיאה בדף הבית
    path('course/<int:course_id>/toggle_favorite/', views.toggle_favorite_course, name='toggle_favorite_course'),

    path('add-course/', views.add_course, name='add_course'),
    # ==========================================
    # הדרייב האישי החדש (מה שהוספנו עכשיו)
    # ==========================================
    path('drive/', personal_drive.personal_drive, name='personal_drive'),

    # ==========================================
    # קהילה ורשת חברתית
    # ==========================================
    path('feed/', views.community_feed, name='community_feed'),
    path('u/<str:username>/', views.public_profile, name='public_profile'),
    path('post/<int:post_id>/like/', views.like_post, name='like_post'),
    path('community/<int:community_id>/join/', views.join_community, name='join_community'),
    path('communities/discover/', views.discover_communities, name='discover_communities'),
    path('post/<int:post_id>/comment/', views.add_comment, name='add_comment'),

    # חיפושים דינמיים ו-API
    path('search/live/', views.live_search, name='live_search'),
    path('ajax/load-majors/', views.load_majors, name='ajax_load_majors'),

    # ניהול קבצים
    path('download/<int:document_id>/', views.download_file, name='download_file'),
    path('document/<int:document_id>/view/', views.document_viewer, name='document_viewer'),
    path('document/<int:document_id>/like/', views.like_document, name='like_document'),
    path('report/<int:document_id>/', views.report_document, name='report_document'),

    #  מחיקה של דברים שהמשתמש יצר
    path('ajax/delete-item/', views.delete_item_ajax, name='delete_item_ajax'),

    # הוספת אוניברסיטה ופקולטה
    path('ajax/add-university/', views.add_university_ajax, name='add_university_ajax'),
    path('ajax/add-major/', views.add_major_ajax, name='add_major_ajax'),

    # פרופיל ואנליטיקס
    path('profile/', views.profile, name='profile'),
    path('complete-profile/', views.complete_profile, name='complete_profile'),
    path('analytics/', views.analytics_dashboard, name='analytics'),

    # הגדרות, פרטיות ונגישות
    path('settings/', views.settings_view, name='settings'),
    path('settings/password/', views.change_password, name='change_password'),
    path('settings/request-data/', views.request_user_data, name='request_user_data'),
    path('settings/delete-account/', views.delete_account, name='delete_account'),
    path('accessibility/', views.accessibility_view, name='accessibility'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('terms/', views.terms_view, name='terms'),

    # סגל אקדמי ושונות
    path('lecturers/', views.lecturers_index, name='lecturers_index'),
    path('staff/<int:staff_id>/rate/', views.rate_staff, name='rate_staff'),
    path('staff/<int:staff_id>/', views.staff_detail, name='staff_detail'),
    path('course/<int:course_id>/set_lecturer/', views.set_semester_lecturer, name='set_semester_lecturer'),
    path('feedback/', views.submit_feedback, name='submit_feedback'),
    path('document/<int:document_id>/ai-summary/', views.summarize_document_ai, name='summarize_document_ai'),
    path('donations/', views.donations, name='donations'),

    # חברות
    path('friend/request/<str:username>/', views.send_friend_request, name='send_friend_request'),
    path('friend/accept/<int:request_id>/', views.accept_friend_request, name='accept_friend_request'),
    path('friend/reject/<int:request_id>/', views.reject_friend_request, name='reject_friend_request'),
    path('my-friends/', views.my_friends, name='my_friends'),
    path('friend/remove/<str:friend_username>/', views.remove_friend, name='remove_friend'),

    path('search/', views.global_search, name='global_search'),
    #path('system-architecture-mirror/', views.agent_report, name='agent_report'),
# ==========================================
    # מערכת התראות
    # ==========================================
    path('notifications/', views.notifications_list, name='notifications_list'),

    # ==========================================
    # סוכן אישי (Personal AI Agent)
    # ==========================================
    #path('agent/upload/', agent_views.upload_agent_file, name='agent_upload_file'),
    #path('agent/ask/', agent_views.ask_agent_question, name='agent_ask_question'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'core.views.error_404'
handler500 = 'core.views.error_500'