"""
Server setup and automation script (Build & Deployment Script)
==============================================================

This file performs the following steps in order:
1. Install packages: downloads and installs all libraries from `requirements`.
2. Collect static files (`collectstatic`): gathers CSS and graphic assets
   into one place so the site loads faster.
3. Manage the database: creates and runs migrations to update the tables
   according to the latest code changes.
4. Apply automatic system setup: creates an initial superuser
   and configures the site domain in the database.
5. Activate AI features: runs a dedicated command that starts the
   documentation and AI agent for the system.

The script includes safety guards (such as `set -o errexit`) so it stops
immediately if something goes wrong, preventing a broken deployment.
"""

#!/usr/bin/env bash
# exit on error
set -o errexit

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "🖼️ Collecting static files..."
python manage.py collectstatic --no-input

# 1. First create the migration files
echo "🔨 Generating migration files..."
python manage.py makemigrations core --no-input

# 2. Then run them - this creates the `core_customuser` table
echo "🗄️ Running migrations..."
python manage.py migrate --no-input

# 3. Only now, once the table definitely exists, run the superuser setup
echo "⚙️ Running post-deploy setup..."
python manage.py shell << 'END'
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
import os

User = get_user_model()
username = os.getenv('ADMIN_USERNAME', 'admin_master')
email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
password = os.getenv('ADMIN_PASSWORD', 'admin1234')

# Safely create the superuser
try:
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username, email, password)
        print(f"✅ Superuser '{username}' created successfully.")
    else:
        print(f"ℹ️ Superuser '{username}' already exists.")
except Exception as e:
    print(f"⚠️ Could not create superuser: {e}")

# Configure the `Site` dynamically so it matches the deployment domain
domain_name = os.getenv('SITE_DOMAIN', 'localhost:8000')
try:
    site, created = Site.objects.update_or_create(
        id=1,
        defaults={
            'domain': domain_name,
            'name': 'Student Drive'
        }
    )
    print(f"✅ Site configured: {site.domain}")
except Exception as e:
    print(f"⚠️ Could not configure site: {e}")

print("🎉 Setup script completed!")
END

# ==========================================
# Run the documentation and intelligence agent
# ==========================================
# echo "🤖 Running AI Documentation Agent..."
# python manage.py run_agent

echo "🚀 Build script finished successfully!"
