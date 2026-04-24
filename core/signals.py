"""
Automatic signals and reactions
===============================
This file handles:
1. Real-time notifications: when a student uploads a new file to a course,
   the system detects it automatically.
2. Smart routing: generates direct notification links that include a hash,
   allowing the frontend to open the exact folder automatically.
3. Audience filtering: sends updates only to students who starred the course,
   while excluding the uploader.
4. Duplicate and error prevention: avoids sending notifications for private
   files, such as chat uploads, or files with no academic course attached.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from .models import Document, Notification, UserCourseSelection
from django.contrib.auth.signals import user_logged_in
from django.utils import timezone
from .utils import process_transaction


@receiver(post_save, sender=Document)
def notify_students_on_new_file(sender, instance, created, **kwargs):
    """
    Run whenever a new `Document` object is created.
    It builds a notification link with a hash so the frontend can open the
    right folder automatically, and safely ignores files with no course.
    """
    # 1. Only act on brand-new files
    if not created:
        return

    # --- Critical guard ---
    # If the file has no course (for example, a chat upload), skip notifications and avoid crashes
    course = instance.course
    if not course:
        print(f"DEBUG: קובץ '{instance.title}' עלה ללא קורס (צ'אט/פרטי). לא נשלחה התראה.")
        return
    # -------------------------

    uploader = instance.uploaded_by
    uploader_name = uploader.username if uploader else "סטודנט"

    # 2. Build the exact target link
    # Append `#folder_ID` so the page JavaScript can open the folder automatically
    if instance.folder:
        base_url = reverse('course_detail_folder', args=[course.id, instance.folder.id])
        target_link = f"{base_url}#folder_{instance.folder.id}"
        print(f"DEBUG: קובץ עלה לתיקייה {instance.folder.id}. לינק מלא נוצר: {target_link}")
    else:
        # If the file was uploaded to the root level
        target_link = reverse('course_detail', args=[course.id])
        print(f"DEBUG: קובץ עלה לשורש הקורס. לינק נוצר: {target_link}")

    # 3. Find all users who starred the course, excluding the uploader
    interested_selections = UserCourseSelection.objects.filter(
        course=course,
        is_starred=True
    )

    if uploader:
        interested_selections = interested_selections.exclude(user=uploader)

    # 4. Prepare the notifications for bulk creation
    notifications_to_create = []
    for selection in interested_selections:
        notifications_to_create.append(
            Notification(
                user=selection.user,
                title=f"חומר חדש ב{course.name}",
                message=f"{uploader_name} העלה/תה את הקובץ: '{instance.title}'",
                link=target_link  # Link with the folder hash suffix
            )
        )

    # 5. Save everything to the database
    if notifications_to_create:
        try:
            Notification.objects.bulk_create(notifications_to_create)
            print(f"DEBUG: נוצרו {len(notifications_to_create)} התראות בהצלחה.")
        except Exception as e:
            print(f"Error creating notifications: {e}")


# ==========================================
# Daily Login Bonus
# ==========================================
@receiver(user_logged_in)
def grant_daily_login_bonus(sender, user, request, **kwargs):
    """מעניק 1 מטבעות למשתמש על התחברות ראשונה באותו יום."""
    # מוודאים שיש למשתמש פרופיל
    if not hasattr(user, 'profile'):
        return

    today = timezone.localtime().date()
    profile = user.profile

    # בודקים אם עדיין לא קיבל בונוס היום
    if profile.last_daily_bonus != today:
        try:
            process_transaction(
                user=user,
                amount=1,
                tx_type='system',
                description="בונוס התחברות יומי! איזה כיף שחזרת אלינו 🎁",
                actor=None,
                notify=True,
                bonus_increases_lifetime=True
            )
            # מעדכנים את תאריך הבונוס להיום ושומרים
            profile.last_daily_bonus = today
            profile.save(update_fields=['last_daily_bonus'])
            print(f"DEBUG: בונוס יומי הוענק בהצלחה ל-{user.username}")
        except Exception as e:
            print(f"Failed to grant daily bonus to {user.username}: {e}")
