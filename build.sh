#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input

# מיגרציה נקייה ורגילה לגמרי!
python manage.py migrate

# הרצת הפקודות המיוחדות שלך
python manage.py load_bgu_courses || true
python manage.py seed_bgu_ee || true

# יצירת מנהל ודומיין
python manage.py shell << END
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
import os

User = get_user_model()
username = os.getenv('ADMIN_USERNAME', 'admin_master')
email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
password = os.getenv('ADMIN_PASSWORD', 'admin1234')

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f"✅ Superuser {username} created.")

Site.objects.filter(id=1).update(domain='student-drive.onrender.com', name='Student Drive')
END#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input

# מיגרציה בלבד - זה רץ מהר
python manage.py migrate

# יצירת מנהל ודומיין (זה לוקח חלקיק שנייה)
python manage.py shell << END
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
import os

User = get_user_model()
username = os.getenv('ADMIN_USERNAME', 'admin_master')
email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
password = os.getenv('ADMIN_PASSWORD', 'admin1234')

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print("✅ Superuser created.")

Site.objects.filter(id=1).update(domain='student-drive.onrender.com', name='Student Drive')
END