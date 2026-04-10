"""
סקריפט הקמה ואוטומציה לשרת (Build & Deployment Script)
=====================================================

הקובץ מבצע את הפעולות הבאות לפי הסדר:
1. התקנת חבילות: מוריד ומתקין את כל הספריות מרשימת ה-requirements.
2. איסוף קבצים סטטיים (collectstatic): מאחד את כל קבצי העיצוב (CSS) 
   והגרפיקה למקום אחד כדי שהאתר ייטען מהר.
3. ניהול מסד הנתונים: יוצר ומריץ "מיגרציות" כדי לעדכן את הטבלאות 
   בבסיס הנתונים בהתאם לשינויים האחרונים בקוד.
4. הגדרות מערכת אוטומטיות: יוצר משתמש מנהל (Superuser) ראשוני 
   ומגדיר את כתובת הדומיין של האתר בבסיס הנתונים.
5. הפעלת בינה מלאכותית: מריץ פקודה מיוחדת המפעילה את סוכן התיעוד 
   וה-AI של המערכת.

הסקריפט כולל מנגנוני הגנה (כמו set -o errexit) שגורמים לו לעצור מיד 
אם משהו השתבש, כדי למנוע מצב של אתר שבור באוויר.
"""

#!/usr/bin/env bash
# exit on error
set -o errexit

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "🖼️ Collecting static files..."
python manage.py collectstatic --no-input

# 1. קודם כל יוצרים את קבצי המיגרציה
echo "🔨 Generating migration files..."
python manage.py makemigrations core --no-input

# 2. עכשיו מריצים אותם - זה יוצר את הטבלה core_customuser
echo "🗄️ Running migrations..."
python manage.py migrate --no-input

# 3. רק עכשיו, כשהטבלה בטוח קיימת, מריצים את ה-Superuser
echo "⚙️ Running post-deploy setup..."
python manage.py shell << 'END'
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
import os

User = get_user_model()
username = os.getenv('ADMIN_USERNAME', 'admin_master')
email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
password = os.getenv('ADMIN_PASSWORD', 'admin1234')

# יצירת סופר-יוזר בצורה בטוחה
try:
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username, email, password)
        print(f"✅ Superuser '{username}' created successfully.")
    else:
        print(f"ℹ️ Superuser '{username}' already exists.")
except Exception as e:
    print(f"⚠️ Could not create superuser: {e}")

# הגדרת ה-Site בצורה דינמית כדי שיתאים ל-DigitalOcean
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
# הפעלת סוכן התיעוד והאינטליגנציה שלנו!
# ==========================================
echo "🤖 Running AI Documentation Agent..."
python manage.py run_agent

echo "🚀 Build script finished successfully!"