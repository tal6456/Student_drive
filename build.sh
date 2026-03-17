#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input

# 1. מריצים מיגרציות רגילות (עם הדילוגים ששמנו קודם כדי לא לקרוס)
python manage.py migrate core 0011 --fake || true
python manage.py migrate core 0012 --fake || true
python manage.py migrate

# 2. יצירה ידנית של טבלת הקהילות (הפתרון לשגיאה שלנו!)
python manage.py shell << END
from django.db import connection
from core.models import Community

try:
    with connection.schema_editor() as editor:
        editor.create_model(Community)
    print("✅ Community table created successfully!")
except Exception as e:
    print("ℹ️ Community table already exists or skipped.")
END

# 3. הרצת הפקודות המיוחדות לקורסים
python manage.py load_bgu_courses || true
python manage.py seed_bgu_ee || true

# 4. יצירת סופר-יוזר ודומיין
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
END