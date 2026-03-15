#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# ניקוי בסיס הנתונים ויצירת מנהל
python manage.py shell << END
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
import os

# 1. יצירת סופר-יוזר
User = get_user_model()
username = os.getenv('ADMIN_USERNAME', 'admin')
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, os.getenv('ADMIN_EMAIL'), os.getenv('ADMIN_PASSWORD'))
    print("Superuser created.")

# 2. עדכון האתר (חשוב!)
site = Site.objects.get_current()
site.domain = 'student-drive.onrender.com'
site.name = 'Student Drive'
site.save()

# 3. ניקוי ה-SocialApp ממסד הנתונים (כדי להשתמש רק בזה שב-settings.py)
SocialApp.objects.filter(provider='google').delete()
print("Database SocialApps cleared to avoid conflicts with settings.py")
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