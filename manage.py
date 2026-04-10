"""
כלי ניהול ושליטה של פרויקט ג'אנגו (Django Management Utility)
===========================================================

מה המטרה של הקובץ הזה?
----------------------
קובץ זה הוא ממשק שורת הפקודה (CLI) של האתר. הוא משמש כצינור המקשר 
בינך לבין תשתית ה-Django, ומאפשר להריץ פעולות תחזוקה, פיתוח וניהול.

הקובץ מאפשר לבצע את הפעולות הבאות:
1. הרצת האתר: הפעלת שרת הפיתוח המקומי (runserver) כדי לבדוק את האתר במחשב.
2. ניהול מסד הנתונים: יצירת טבלאות (makemigrations) ועדכונן (migrate) 
   בהתאם לשינויים שביצעת במודלים.
3. יצירת משתמשים: יצירת משתמשי על (createsuperuser) לניהול האתר.
4. הרצת פקודות מותאמות אישית: הפעלת סקריפטים מיוחדים שבנית עבור 
   Student Drive, כמו הרצת סוכן ה-AI או ניקוי נתונים.
5. בדיקות (Testing): הרצת בדיקות אוטומטיות לווידוא שהקוד תקין.

חשוב לזכור: הקובץ הזה טוען באופן אוטומטי את קובץ ה-Settings של הפרויקט, 
ולכן הוא תמיד יודע לאיזה בסיס נתונים להתחבר ואיך להפעיל את האפליקציה.
"""

#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'student_drive.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
