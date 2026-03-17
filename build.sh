#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input

# --- התיקון שלנו למיגרציות שמתנגשות (קורה פעם אחת ואז נשאר מסודר) ---
python manage.py migrate core 0011 --fake || true
python manage.py migrate core 0012 --fake || true

# מריץ את שאר המיגרציות התקינות (כולל יצירת הקהילות!)
python manage.py migrate

# הרצת הפקודות המיוחדות שלך רק אם הן קיימות
python manage.py load_bgu_courses || true
python manage.py seed_bgu_ee || true

python manage.py shell << END
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
import os

# יצירת סופר-יוזר בצורה בטוחה
User = get_user_model()
username = os.getenv('ADMIN_USERNAME', 'admin_master')
email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
password = os.getenv('ADMIN_PASSWORD', 'admin1234')

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f"Superuser {username} created.")

# עדכון דומיין האתר
Site.objects.filter(id=1).update(domain='student-drive.onrender.com', name='Student Drive')
END