from django.contrib import admin
from django.urls import path, include  # חובה לייבא את include!
from core import views
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- הנה השורה החסרה שמוסיפה את כל נתיבי ההרשמה והאבטחה ---
    path('accounts/', include('allauth.urls')),

    path('', views.home, name='home'),
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('analytics/', views.analytics_dashboard, name='analytics'),
    path('terms/', TemplateView.as_view(template_name='core/terms.html'), name='terms'),
    path('download/<int:document_id>/', views.download_file, name='download_file'),
    path('profile/', views.profile, name='profile'),

    # הנתיבים הישנים (שמתי אותם בהערה כדי שלא יתנגשו עם המערכת החדשה)
    # path('register/', views.register, name='register'),
    # path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    # path('logout/', views.logout_view, name='logout'),
]

# מאפשר להציג קבצים שהועלו (Media) בזמן פיתוח
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)