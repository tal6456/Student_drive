from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.urls import reverse


class CustomAccountAdapter(DefaultAccountAdapter):
    def get_signup_redirect_url(self, request):
        # מופעל רק כשמשתמש חדש נרשם עם אימייל וסיסמה פעם ראשונה
        return reverse('complete_profile')

    def get_login_redirect_url(self, request):
        # מופעל בכל פעם שיש התחברות (בין אם רגילה ובין אם חיבור אוטומטי של גוגל למשתמש קיים)
        user = request.user

        # הלוגיקה החכמה: בודק אם הפרופיל חסר פרטים בסיסיים (למשל, שם פרטי)
        # אם אין לו שם פרטי, זה אומר שהוא בחיים לא סיים את טופס "השלמת פרטים"
        if not user.first_name:
            return reverse('complete_profile')

        # אם יש לו הכל, ברוך הבא לדף הבית!
        return reverse('home')


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def get_signup_redirect_url(self, request, sociallogin):
        # מופעל רק כשמשתמש חדש נרשם דרך גוגל פעם ראשונה (שים לב שהוספנו את sociallogin)
        return reverse('complete_profile')