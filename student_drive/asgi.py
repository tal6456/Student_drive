"""
הקובץ מטפל ב:
1. תמיכה בפעולות אסינכרוניות: מאפשר לאתר לטפל בכמות גדולה של בקשות במקביל 
   ביעילות רבה יותר.
2. הכנה לתקשורת בזמן אמת: זהו הבסיס להוספת יכולות כמו צ'אט חי (WebSockets), 
   התראות דחיפה (Push Notifications) ועדכונים חיים ללא רענון דף.
3. חיבור להגדרות הפרויקט: הקובץ מקשר את השרת לקובץ ה-Settings של Student Drive 
   כדי שהמערכת תדע איך להריץ את האפליקציה.

בדרך כלל לא נוגעים בקובץ זה ביומיום, אך הוא קריטי ברגע שמעלים את האתר 
לאוויר (Deployment) או כשרוצים להפוך את האתר לאינטראקטיבי בזמן אמת.
"""

"""
ASGI config for student_drive project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""


import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'student_drive.settings')

application = get_asgi_application()
