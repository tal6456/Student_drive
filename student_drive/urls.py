from django.contrib import admin
from django.urls import path, include
from core import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ממשק ניהול
    path('admin/', admin.site.urls),

    # מערכת ההרשמה והתחברות (Allauth)
    path('accounts/', include('allauth.urls')),

    # דפי ניווט וקורסים
    path('', views.home, name='home'),
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('add-course/', views.add_course, name='add_course'),
    path('course/<int:course_id>/folder/<int:folder_id>/', views.course_detail, name='course_detail_folder'),

    # ==========================================
    # קהילה ורשת חברתית (הנתיבים החדשים!)
    # ==========================================
    path('feed/', views.community_feed, name='community_feed'),
    path('u/<str:username>/', views.public_profile, name='public_profile'),  # פרופיל ציבורי
    path('post/<int:post_id>/like/', views.like_post, name='like_post'),  # לייק לפוסט (AJAX)

    # חיפושים דינמיים ו-API
    path('search/live/', views.live_search, name='live_search'),
    path('ajax/load-majors/', views.load_majors, name='ajax_load_majors'),

    # ניהול קבצים
    path('download/<int:document_id>/', views.download_file, name='download_file'),
    path('document/<int:document_id>/like/', views.like_document, name='like_document'),

    path('report/<int:document_id>/', views.report_document, name='report_document'),

    # פרופיל ואנליטיקס (של המשתמש המחובר)
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

    # מרצים ושונות
    path('lecturers/', views.lecturers_index, name='lecturers_index'),
    path('lecturers/<int:lecturer_id>/rate/', views.rate_lecturer, name='rate_lecturer'),
    path('course/<int:course_id>/set_lecturer/', views.set_semester_lecturer, name='set_semester_lecturer'),
    path('feedback/', views.submit_feedback, name='submit_feedback'),
    path('document/<int:document_id>/ai-summary/', views.summarize_document_ai, name='summarize_document_ai'),
    path('donations/', views.donations, name='donations'),

    # שליחה בקשה ודחייה של חברות
    path('friend/request/<str:username>/', views.send_friend_request, name='send_friend_request'),
    path('friend/accept/<int:request_id>/', views.accept_friend_request, name='accept_friend_request'),
    path('friend/reject/<int:request_id>/', views.reject_friend_request, name='reject_friend_request'),

    path('search/', views.global_search, name='global_search'),

    path('my-friends/', views.my_friends, name='my_friends'),
    path('friend/remove/<str:friend_username>/', views.remove_friend, name='remove_friend'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)