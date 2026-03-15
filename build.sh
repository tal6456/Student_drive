#!/usr/bin/env bash
# exit on error
set -o errexit

# 1. התקנת ספריות
pip install -r requirements.txt

# 2. איסוף קבצים סטטיים והרצת מיגרציות
python manage.py collectstatic --no-input
python manage.py migrate

# 3. טעינת נתוני האוניברסיטאות והקורסים (הקבצים שיצרת)
#python manage.py load_bgu_courses
python manage.py seed_bgu_ee

# 4. הגדרות אוטומטיות בתוך ה-Shell (מנהל מערכת וניקוי גוגל)
python manage.py shell << END
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
import os

# יצירת סופר-יוזר
User = get_user_model()
username = os.getenv('ADMIN_USERNAME', 'admin')
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, os.getenv('ADMIN_EMAIL'), os.getenv('ADMIN_PASSWORD'))
    print("Superuser created.")

# עדכון הגדרות האתר
site, created = Site.objects.get_current(), False
site.domain = 'student-drive.onrender.com'
site.name = 'Student Drive'
site.save()

# ניקוי שאריות גוגל כדי להשתמש ב-settings.py
SocialApp.objects.filter(provider='google').delete()
print("SocialApps cleared and DB seeded.")
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