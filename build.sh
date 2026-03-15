#!/usr/bin/env bash
# exit on error
set -o errexit

# 1. התקנת ספריות
pip install -r requirements.txt

# 2. איסוף קבצים סטטיים והרצת מיגרציות
python manage.py collectstatic --no-input
python manage.py migrate

# 3. הגדרות אוטומטיות בתוך בסיס הנתונים (מנהל מערכת וחיבור גוגל)
python manage.py shell << END
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
import os

# --- יצירת סופר-יוזר ---
User = get_user_model()
username = os.getenv('ADMIN_USERNAME', 'admin')
email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
password = os.getenv('ADMIN_PASSWORD', 'admin123')

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f"Superuser {username} created.")
else:
    print(f"Superuser {username} already exists.")

# --- עדכון הגדרות האתר (Site) ---
# חשוב כדי שגוגל ידע לאן לחזור אחרי ההתחברות
site = Site.objects.get_current()
site.domain = 'student-drive.onrender.com'
site.name = 'Student Drive'
site.save()

# --- הגדרת גוגל (SocialApp) - מניעת כפילויות ---
client_id = os.getenv('GOOGLE_CLIENT_ID')
secret = os.getenv('GOOGLE_CLIENT_SECRET')

if client_id and secret:
    # מוחקים הגדרות קודמות של גוגל כדי למנוע MultipleObjectsReturned
    SocialApp.objects.filter(provider='google').delete()

    # יוצרים הגדרה אחת חדשה ותקינה
    app = SocialApp.objects.create(
        provider='google',
        name='Google Login',
        client_id=client_id,
        secret=secret
    )
    app.sites.add(site)
    app.save()
    print("SocialApp for Google configured cleanly.")
else:
    print("Skipping SocialApp config: Environment variables missing.")

END
#מה שהיה מקודם לפני הריינדר
#!/usr/bin/env bash
## exit on error
#set -o errexit
#
#pip install -r requirements.txt
#python manage.py collectstatic --no-input
#python manage.py migrate
#
#python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='$ADMIN_USERNAME').exists() or User.objects.create_superuser('$ADMIN_USERNAME', '$ADMIN_EMAIL', '$ADMIN_PASSWORD')"