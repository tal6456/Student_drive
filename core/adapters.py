from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.urls import reverse

class CustomAccountAdapter(DefaultAccountAdapter):
    def get_signup_redirect_url(self, request):
        # מופעל רק כשמשתמש חדש נרשם עם אימייל וסיסמה
        return reverse('complete_profile')

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def get_signup_redirect_url(self, request):
        # מופעל רק כשמשתמש חדש נרשם דרך גוגל פעם ראשונה
        return reverse('complete_profile')