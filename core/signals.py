from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from .models import Document, Notification, UserCourseSelection


@receiver(post_save, sender=Document)
def notify_students_on_new_file(sender, instance, created, **kwargs):
    """
    הסיגנל הזה רץ בכל פעם שנוצר אובייקט Document חדש.
    הוא יוצר התראה עם לינק שכולל Hash כדי לפתוח את התיקייה ב-Frontend.
    כעת הוא תומך גם בקבצים ללא קורס (כמו בצ'אט) ופשוט מתעלם מהם.
    """
    # 1. פועלים רק ביצירה של קובץ חדש
    if not created:
        return

    # --- התיקון הקריטי כאן ---
    # אם הקובץ עלה ללא קורס (למשל בצ'אט), אנחנו לא רוצים לשלוח התראות ולא רוצים לקרוס
    course = instance.course
    if not course:
        print(f"DEBUG: קובץ '{instance.title}' עלה ללא קורס (צ'אט/פרטי). לא נשלחה התראה.")
        return
    # -------------------------

    uploader = instance.uploaded_by
    uploader_name = uploader.username if uploader else "סטודנט"

    # 2. בניית הלינק המדויק
    # אנחנו מוסיפים #folder_ID בסוף כדי שה-JavaScript בדף ידע לפתוח את התיקייה אוטומטית
    if instance.folder:
        base_url = reverse('course_detail_folder', args=[course.id, instance.folder.id])
        target_link = f"{base_url}#folder_{instance.folder.id}"
        print(f"DEBUG: קובץ עלה לתיקייה {instance.folder.id}. לינק מלא נוצר: {target_link}")
    else:
        # אם הקובץ עלה לשורש (Root)
        target_link = reverse('course_detail', args=[course.id])
        print(f"DEBUG: קובץ עלה לשורש הקורס. לינק נוצר: {target_link}")

    # 3. מציאת כל המשתמשים שסימנו את הקורס בכוכב (והחרגת המעלה)
    interested_selections = UserCourseSelection.objects.filter(
        course=course,
        is_starred=True
    )

    if uploader:
        interested_selections = interested_selections.exclude(user=uploader)

    # 4. הכנת רשימת ההתראות ליצירה מרוכזת
    notifications_to_create = []
    for selection in interested_selections:
        notifications_to_create.append(
            Notification(
                user=selection.user,
                title=f"חומר חדש ב{course.name}",
                message=f"{uploader_name} העלה/תה את הקובץ: '{instance.title}'",
                link=target_link  # הלינק עם ה-Hash בסוף
            )
        )

    # 5. שמירה בבסיס הנתונים
    if notifications_to_create:
        try:
            Notification.objects.bulk_create(notifications_to_create)
            print(f"DEBUG: נוצרו {len(notifications_to_create)} התראות בהצלחה.")
        except Exception as e:
            print(f"Error creating notifications: {e}")