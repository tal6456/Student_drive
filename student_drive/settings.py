"""
Django settings for student_drive project.
"""
from dotenv import load_dotenv
from pathlib import Path
import os
from django.utils.translation import gettext_lazy as _
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(os.path.join(BASE_DIR, '.env'))
# --- אבטחה: מפתח סודי ---
SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true' # להחזיר שאני רוצה לעבוד על האינטרנט

# --- מפתח AI של גוגל ---
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')



#TODO
# הגדרת דומיינים מורשים (Localhost + DigitalOcean + Render למקרה גיבוי)
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver', '.ondigitalocean.app', 'student-drive.onrender.com']

# ==========================================
# הגדרות שליחת מיילים (דרך ג'ימייל)
# ==========================================
# רשימת המנהלים שיקבלו מייל בכל פעם שיש שגיאת 500
ADMINS = [
    ('Tal', 'student.drive10@gmail.com'),
    ('KOZO', 'amitkozo5528@gmail.com') # קוזו תעדכן את המייל הרישמי שלך
]

# המייל שממנו יישלחו ההודעות (יכול להיות אותו מייל)
SERVER_EMAIL = 'student.drive10@gmail.com'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'student.drive10@gmail.com'
# כאן שמים סיסמת אפליקציה של גוגל, לא את הסיסמה הרגילה שלך! עדיף להשתמש במשתנה סביבה:
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
X_FRAME_OPTIONS = 'SAMEORIGIN'


# מאפשר הזרקת דומיין מותאם אישית (Custom Domain) דרך משתני סביבה
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

    # Apps שלנו
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

# נסיון לקרוא DATABASE_URL מהסביבה (Render) או מה-.env (מקומי)
DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL', f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
        conn_max_age=600
    )
}

# ==========================================
# אבטחת סיסמאות (הצפנה משופרת)
# ==========================================
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher', # ההצפנה הכי חזקה
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
# אבטחת עוגיות וסשנים (הגנה מגניבת זהות)
# ==========================================
SESSION_COOKIE_HTTPONLY = True  # מונע מ-JS לגשת לסשן
CSRF_COOKIE_HTTPONLY = True     # מונע מ-JS לגשת ל-CSRF
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
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles') # התיקייה שהשרת יאסוף אליה את העיצוב

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# --- הגדרות אימות ---
AUTH_USER_MODEL = 'core.CustomUser'
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

LOGIN_URL = 'account_login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'

ACCOUNT_LOGIN_METHODS = {'email', 'username'}
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = "none"
SOCIALACCOUNT_EMAIL_VERIFICATION = "none"

ACCOUNT_LOGOUT_ON_GET = False
SOCIALACCOUNT_LOGIN_ON_GET = False

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
ACCOUNT_SIGNUP_FORM_CLASS = 'core.forms.CustomSignupForm'

# ==========================================
# Allauth Adapters & Social Auto-Connect
# ==========================================
# הפניית משתמשים חדשים למסך השלמת פרופיל
ACCOUNT_ADAPTER = 'core.adapters.CustomAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'core.adapters.CustomSocialAccountAdapter'

# חיבור אוטומטי של גוגל לאימייל קיים (ללא מסך שגיאה)
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True
# דילוג על טופס יצירת משתמש בהתחברות דרך גוגל
SOCIALACCOUNT_AUTO_SIGNUP = True

# -----------------------------------------------------------
# -----------------------------------------------------------
if not DEBUG:
    # מאלץ את כל התעבורה לעבור דרך HTTPS
    SECURE_SSL_REDIRECT = True

    # ==========================================
    # אבטחת עוגיות וסשנים (הגנה מגניבת זהות)
    # ==========================================
    SESSION_COOKIE_HTTPONLY = True  # משאירים על True, זה קריטי לאבטחת הסשן!
    CSRF_COOKIE_HTTPONLY = True  # תוקן ל - True. ה-JS ב-base.html עוקף את זה דרך ה-DOM.

    CSRF_TRUSTED_ORIGINS = ['https://*.ondigitalocean.app', 'https://student-drive.onrender.com']

    # HSTS - אומר לדפדפן "תמיד תתחבר אלי ב-HTTPS"
    SECURE_HSTS_SECONDS = 31536000  # שנה אחת
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
        # אופציונלי אבל מומלץ מאוד לאבטחה בגרסאות החדשות של ג'נגו
        'OAUTH_PKCE_ENABLED': True,
    }
}

# מוודא שהמערכת מחפשת את הנתונים בטבלאות האדמין ולא בקוד
SOCIALACCOUNT_STORE_TOKENS = True

# ==========================================
# הגדרות אמזון S3 (חכמות - עובדות לפי משתני סביבה)
# ==========================================
if os.getenv('AWS_ACCESS_KEY_ID'):
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME')

    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    AWS_QUERYSTRING_AUTH = False

    # --- השיטה המודרנית לג'אנגו 4.2 ומעלה ---
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }