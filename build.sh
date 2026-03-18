#!/usr/bin/env bash
# exit on error
set -o errexit

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "🖼️ Collecting static files..."
python manage.py collectstatic --no-input

# --- הוספנו את השורה הזו כדי לפתור את השגיאה ---
echo "🔨 Generating migration files..."
python manage.py makemigrations core --no-input

echo "🗄️ Running migrations..."
python manage.py migrate --no-input

echo "⚙️ Running post-deploy setup (Superuser, Site config, etc.)..."
python manage.py shell << 'END'
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
import os

# --- 1. Create Superuser ---
User = get_user_model()
username = os.getenv('ADMIN_USERNAME', 'admin_master')
email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
password = os.getenv('ADMIN_PASSWORD', 'admin1234')

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f"✅ Superuser '{username}' created successfully.")
else:
    print(f"ℹ️ Superuser '{username}' already exists.")

# --- 2. Configure Django Sites (for allauth/Google) ---
site, created = Site.objects.update_or_create(
    id=1,
    defaults={
        'domain': 'student-drive.onrender.com',
        'name': 'Student Drive'
    }
)
print(f"✅ Site configured: {site.domain}")

print("🎉 Setup script completed successfully!")
END

echo "🚀 Build script finished successfully!"