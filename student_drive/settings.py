"""
Django settings for student_drive project.
"""

from pathlib import Path
import os
from django.utils.translation import gettext_lazy as _  # הוספנו למען מנוע התרגום

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-up1@h&nik=hd!*j@xbv$uk9w0z631t5f-vt&sk^*afmtyu6ng%'

DEBUG = True

ALLOWED_HOSTS = []

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    # Apps שלנו
    'core',

    # Allauth & Social Accounts
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]

SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # <--- מנוע השפות הוסף כאן!
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'student_drive.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # מונה דיווחים למנהלים
                'core.context_processors.pending_reports_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'student_drive.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ==========================================
# Internationalization (שפות ותרגום)
# ==========================================
LANGUAGE_CODE = 'he'
TIME_ZONE = 'Asia/Jerusalem'
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ('he', _('Hebrew')),
    ('en', _('English')),
    ('ar', _('Arabic')),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# ==========================================
# Static & Media
# ==========================================
STATIC_URL = 'static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# --- הגדרות אימות (Allauth) - גרסה נקייה ללא Conflict ---

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

LOGIN_URL = 'account_login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'

# הגדרת שיטות ההתחברות (מייל ושם משתמש)
ACCOUNT_LOGIN_METHODS = {'email', 'username'}

# חובה להגדיר אימייל ולוודא שהוא ייחודי
ACCOUNT_UNIQUE_EMAIL = True

# ביטול ה-Conflict: לא מגדירים כאן מייל או שם משתמש כי הם כבר ב-Methods למעלה
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']

# הגדרות אימות מייל (בוטל לנוחות עם גוגל)
ACCOUNT_EMAIL_VERIFICATION = "none"
SOCIALACCOUNT_EMAIL_VERIFICATION = "none"

# התחברות מהירה
ACCOUNT_LOGOUT_ON_GET = True
SOCIALACCOUNT_LOGIN_ON_GET = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# חיבור טופס ההרשמה המותאם שלנו (כולל אישור תנאי השימוש)
ACCOUNT_SIGNUP_FORM_CLASS = 'core.forms.CustomSignupForm'

# הגדרות שליחת אימיילים
# כרגע, המיילים "ישלחו" ויודפסו בטרמינל שלך כדי שתוכל לראות שזה עובד בלי להסתבך עם סיסמאות של Gmail.
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'admin@studentdrive.com'

# מאפשר תצוגה מקדימה של קבצי PDF בתוך האתר שלנו
X_FRAME_OPTIONS = 'SAMEORIGIN'

handler404 = 'core.views.error_404'
handler500 = 'core.views.error_500'