#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# יצירת מנהל מערכת וחיבור גוגל באופן אוטומטי
python manage.py shell << END
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
import os

# 1. יצירת סופר-יוזר
User = get_user_model()
username = os.getenv('ADMIN_USERNAME', 'admin')
email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
password = os.getenv('ADMIN_PASSWORD', 'admin123')
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f"Superuser {username} created.")

# 2. עדכון שם האתר
site = Site.objects.get_current()
site.domain = 'student-drive.onrender.com'
site.name = 'Student Drive'
site.save()

# 3. יצירת חיבור לגוגל (SocialApp)
client_id = os.getenv('GOOGLE_CLIENT_ID')
secret = os.getenv('GOOGLE_CLIENT_SECRET')

if client_id and secret:
    app, created = SocialApp.objects.get_or_create(provider='google', name='Google Login')
    app.client_id = client_id
    app.secret = secret
    app.sites.add(site)
    app.save()
    print("SocialApp for Google configured.")
END


#!/usr/bin/env bash
## exit on error
#set -o errexit
#
#pip install -r requirements.txt
#python manage.py collectstatic --no-input
#python manage.py migrate
#
#python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='$ADMIN_USERNAME').exists() or User.objects.create_superuser('$ADMIN_USERNAME', '$ADMIN_EMAIL', '$ADMIN_PASSWORD')"