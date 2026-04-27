import os
from celery import Celery

# מגדיר ל-Celery באיזה קובץ הגדרות להשתמש
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'student_drive.settings')

app = Celery('student_drive')

# קורא את ההגדרות מה-settings.py (כל מה שמתחיל ב-CELERY_)
app.config_from_object('django.conf:settings', namespace='CELERY')

# מחפש אוטומטית קבצי tasks.py בכל ה-apps שלך
app.autodiscover_tasks()