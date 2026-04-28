"""
Project core settings
=====================

What is this file for?
----------------------
This file is the site's control center. It wires together the major system
components, including the database, email server, cloud storage, and security.

It covers five critical areas:
1. Security: secret keys, HTTPS settings, and strong password hashing.
2. Environment handling (`DEBUG`): separates local development from live deployment.
3. Data infrastructure: configures the database and S3-based file storage.
4. Authentication and Google login: defines social-login behavior.
5. Communication and languages: configures outgoing mail and language support.

Changes in this file affect the stability and security of the whole system,
so edits here should be made carefully, especially when moving between
development and production. Never commit secret keys.
"""

"""
Django settings for student_drive project.
"""
from dotenv import load_dotenv
from pathlib import Path
import os
import sys
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(os.path.join(BASE_DIR, '.env'), override=True)
# --- Security: secret key ---
SECRET_KEY = os.getenv('SECRET_KEY')
is_running_tests = (
    any(arg in {'test', 'pytest', 'py.test'} for arg in sys.argv)
    or bool(os.getenv('PYTEST_CURRENT_TEST'))
)
if not SECRET_KEY and is_running_tests:
    SECRET_KEY = 'test-secret-key'
if not SECRET_KEY:
    raise ImproperlyConfigured('SECRET_KEY environment variable is required.')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'  # Toggle this when switching between local and deployed work

# --- Google AI key ---
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')



#TODO
# Allowed domains (localhost + DigitalOcean + Render as a fallback)
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver', '.ondigitalocean.app', 'student-drive.onrender.com']

# ==========================================
# Email delivery settings (via Gmail)
# ==========================================
# Admins who receive an email whenever a 500 error occurs
ADMINS = [
    ('Tal', 'student.drive10@gmail.com'),
]

# Sender address for outgoing emails
SERVER_EMAIL = 'student.drive10@gmail.com'

# Smart environment-aware email backend selection
if DEBUG:
    # בסביבת פיתוח, שומר את המיילים כקבצי טקסט קריאים בתיקייה (למניעת קידודי Base64 בעברית)
    EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
    EMAIL_FILE_PATH = BASE_DIR / "sent_emails"
else:
    # In production, send real emails to the student's inbox
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'student.drive10@gmail.com'
# Use a Google app password here, not your normal Gmail password; an environment variable is preferred
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
X_FRAME_OPTIONS = 'SAMEORIGIN'


# Allow an optional custom domain through environment variables
APP_DOMAIN = os.getenv('APP_DOMAIN')
if APP_DOMAIN:
    ALLOWED_HOSTS.append(APP_DOMAIN)

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'storages',

    # Our apps
    'core',

    # Allauth & Social Accounts
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'django_cleanup.apps.CleanupConfig',
]

SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'core.middleware.ProfileCompletionMiddleware',
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
                'core.context_processors.global_counts',
            ],
        },
    },
]

WSGI_APPLICATION = 'student_drive.wsgi.application'

# Try reading `DATABASE_URL` from the environment or `.env`
DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL', f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
        conn_max_age=600
    )
}

# ==========================================
# Password security
# ==========================================
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',  # Strongest hashing option in this stack
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ==========================================
# Cookie and session security
# ==========================================
SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access to the session cookie
CSRF_COOKIE_HTTPONLY = True     # Prevent JavaScript access to the CSRF cookie
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# ==========================================
# Internationalization
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
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # Folder where the server collects static assets

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# --- Authentication settings ---
AUTH_USER_MODEL = 'core.CustomUser'
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

LOGIN_URL = 'account_login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'

# --- Authentication & Registration Settings ---
ACCOUNT_LOGIN_METHODS = {'email', 'username'}
ACCOUNT_UNIQUE_EMAIL = True

# חובה לאשר מייל למשתמשים שנרשמים עם סיסמה (מונע ספאם)
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']

# לא מאפשר התחברות לפני לחיצה על הלינק באימייל
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True

# פטור מאימות למשתמשי גוגל (הם מאומתים מול גוגל)
SOCIALACCOUNT_EMAIL_VERIFICATION = "none"

ACCOUNT_LOGOUT_ON_GET = False
SOCIALACCOUNT_LOGIN_ON_GET = False

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
ACCOUNT_SIGNUP_FORM_CLASS = 'core.forms.CustomSignupForm'

# ==========================================
# Allauth Adapters & Social Auto-Connect
# ==========================================
# Redirect new users to the profile completion screen
ACCOUNT_ADAPTER = 'core.adapters.CustomAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'core.adapters.CustomSocialAccountAdapter'

# Automatically connect Google login to an existing email without an error screen
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True
# Skip the extra signup form during Google login
SOCIALACCOUNT_AUTO_SIGNUP = True

# -----------------------------------------------------------
# -----------------------------------------------------------
if not DEBUG:
    # Force all traffic through HTTPS
    SECURE_SSL_REDIRECT = True

    # ==========================================
    # Cookie and session security
    # ==========================================
    SESSION_COOKIE_HTTPONLY = True  # Keep this `True`; it is critical for session security
    CSRF_COOKIE_HTTPONLY = True  # Intentionally `True`; client-side code reads the token from the DOM

    CSRF_TRUSTED_ORIGINS = ['https://*.ondigitalocean.app', 'https://student-drive.onrender.com', 'https://student-drive-8d8o9.ondigitalocean.app']

    # HSTS tells the browser to always connect over HTTPS
    SECURE_HSTS_SECONDS = 31536000  # One year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True


# ==========================================
# Google Social Auth Configuration
# ==========================================
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        # Optional, but strongly recommended for security in newer Django versions
        'OAUTH_PKCE_ENABLED': True,
    }
}

# Store social-account tokens in the database instead of hardcoding anything in code
SOCIALACCOUNT_STORE_TOKENS = True

# ==========================================
# Amazon S3 settings driven by environment variables
# ==========================================
if os.getenv('AWS_ACCESS_KEY_ID'):
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME')

    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    AWS_QUERYSTRING_AUTH = False

# הגדרת ברירת מחדל (מקומי)
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# אם יש הגדרות S3, נדרוס רק את ה-default
if os.getenv('AWS_ACCESS_KEY_ID'):
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    # ... שאר הגדרות ה-AWS שלך ...

    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    }
# ==========================================
# Celery & Redis Configuration (Background Tasks)
# ==========================================
# שואב את כתובת הרדיס ממשתני הסביבה (בייצור) או משתמש בברירת מחדל מקומית
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_ALWAYS_EAGER = True