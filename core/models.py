"""
Core data models
================

This file defines the application's data structure, entity hierarchy,
and relationships between objects.

It covers four critical areas:
1. Entity definitions: the fields for objects such as users, courses, and documents.
2. Relationships: how the data connects through foreign keys and many-to-many links.
3. Internal logic: helper methods that compute or maintain model state.
4. Validation: rules such as required fields and file-size limits.

Changes in this file usually require `makemigrations` and `migrate`
to update the database schema.
"""

from django.db import models, IntegrityError, transaction
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.urls import reverse
from django.utils.text import slugify
import os
import random
import string
import uuid
from .utils import compress_to_webp, validate_file_size
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User
from .utils import compress_to_webp, validate_file_size, validate_file_type

# ==========================================
# 0. User system (RBAC - Role Based Access Control)
# ==========================================

custom_username_validator = RegexValidator(
    regex=r'^[\w.@+\- ]+$',
    message='שם משתמש יכול להכיל אותיות, מספרים, רווחים, ותווים מיוחדים (@/./+/-/_).'
)
TAG_CHOICES = [
    ('none', 'ללא תיוג'),
    ('urgent', 'חומר עזר'),
    ('exam', 'למבחן'),
    ('summary', 'סיכום'),
    ('important', 'חשוב'),
]

NEW_USER_STARTING_COINS = 10

def generate_referral_code():
    """Generate a random referral code made of letters and digits."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

class CustomUser(AbstractUser):
    """
    Primary user model that replaces Django's default user model.
    It manages authentication and system permissions.
    """
    ROLE_CHOICES = (
        ('member', 'חבר/ת קהילה'),  # Students, lecturers, and regular users
        ('moderator', 'איש/אשת צוות'),  # Staff or volunteer moderators
        ('admin', 'מנהל/ת העל'),  # Platform administrator
    )

    username = models.CharField(
        max_length=150, unique=True, validators=[custom_username_validator],
        error_messages={'unique': "משתמש עם שם זה כבר קיים במערכת."},
    )

    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='member', verbose_name="תפקיד המשתמש")

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class UserProfile(models.Model):
    """Unified user profile model for students, lecturers, and general users."""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')

    # --- Academic information (optional, mainly for students) ---
    university = models.ForeignKey('University', on_delete=models.SET_NULL, null=True, blank=True,
                                   verbose_name="מוסד לימודים")
    major = models.ForeignKey('Major', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="מסלול לימודים")
    YEAR_CHOICES = [(1, 'שנה א\''), (2, 'שנה ב\''), (3, 'שנה ג\''), (4, 'שנה ד\''), (5, 'שנה ה\' / תואר שני')]
    year = models.IntegerField(choices=YEAR_CHOICES, null=True, blank=True, verbose_name="שנת לימוד")

    # --- Personal details ---
    bio = models.TextField(max_length=500, blank=True, verbose_name="קצת עלי (Bio)")
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True, verbose_name="תמונת פרופיל", validators=[validate_file_size])
    phone_number = models.CharField(max_length=15, blank=True, null=True, verbose_name="מספר טלפון")

    # --- Economy and reputation ---
    current_balance = models.PositiveIntegerField(default=0, verbose_name="יתרת מטבעות לשימוש")
    lifetime_coins = models.PositiveIntegerField(default=0, verbose_name="מוניטין (סך כל המטבעות שהורווחו מעשייה)")
    last_daily_bonus = models.DateField(null=True, blank=True, verbose_name="תאריך בונוס יומי אחרון")

    favorite_courses = models.ManyToManyField('Course', related_name='favorited_by_users', blank=True,
                                              verbose_name="קורסים מועדפים")

    # --- User preferences ---
    THEME_CHOICES = [('light', 'יום (בהיר)'), ('dark', 'לילה (כהה)')]
    LANGUAGE_CHOICES = [('he', 'עברית'), ('en', 'English')]
    VISIBILITY_CHOICES = [
        ('public', 'כולם יכולים לראות את הפרופיל שלי'),
        ('users_only', 'רק משתמשים מחוברים יכולים לראות'),
        ('private', 'אף אחד (פרופיל פרטי)')
    ]

    theme_preference = models.CharField(max_length=10, choices=THEME_CHOICES, default='auto', verbose_name="ערכת נושא")
    language_preference = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='he', verbose_name="שפה")
    profile_visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='public',
                                          verbose_name="מי יכול לראות את הפרופיל שלי")
    show_coins_publicly = models.BooleanField(default=True, verbose_name="הצג מוניטין לציבור")

    # --- Referral fields ---
    referral_code = models.CharField(max_length=12, unique=True, blank=True, null=True)
    referred_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='referrals')

    @property
    def rank_name(self):
        """Compute the user's rank using lifetime coins only, not the current balance."""
        if self.lifetime_coins >= 1000:
            return "💎 אלוף דרייב"
        elif self.lifetime_coins >= 500:
            return "🏆 אגדת סיכומים"
        elif self.lifetime_coins >= 200:
            return "🥇 עורך נאמן"
        elif self.lifetime_coins >= 50:
            return "🥈 תורם פעיל"
        return "🥉 מתלמד"

    # --- Economy helpers ---
    # def earn_coins(self, amount):
    #     """Award coins earned through activity, increasing both balance and reputation."""
    #     self.current_balance += amount
    #     self.lifetime_coins += amount
    #     self.save()
    #
    # def buy_coins(self, amount):
    #     """Handle a coin purchase, increasing balance only and not reputation."""
    #     self.current_balance += amount
    #     self.save()
    #
    # def spend_coins(self, amount):
    #     """Spend coins by decreasing the current balance only."""
    #     if self.current_balance >= amount:
    #         self.current_balance -= amount
    #         self.save()
    #         return True
    #     return False

    def __str__(self):
        return self.user.username

    def save(self, *args, **kwargs):
        # Generate a referral code if it does not exist yet
        if not self.referral_code:
            self.referral_code = generate_referral_code()

        # --- Compress the profile picture to WebP ---
        if self.profile_picture and not self.profile_picture.name.endswith('.webp'):
            self.profile_picture = compress_to_webp(self.profile_picture)

        super().save(*args, **kwargs)

    @property
    def pending_friend_requests(self):
        return self.user.received_requests.filter(status='pending')

    @property
    def get_accepted_friends(self):
        from django.db import models
        relations = Friendship.objects.filter(
            (models.Q(user_from=self.user) | models.Q(user_to=self.user)),
            status='accepted'
        )
        friends = []
        for rel in relations:
            if rel.user_from == self.user:
                friends.append(rel.user_to)
            else:
                friends.append(rel.user_from)
        return friends


@receiver(post_save, sender=CustomUser)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    """Create a profile automatically for every new user, using the safe path."""
    if created:
        UserProfile.objects.create(
            user=instance,
            current_balance=NEW_USER_STARTING_COINS,
            lifetime_coins=NEW_USER_STARTING_COINS,
        )
        # Notification for initial 10 coins is sent in complete_profile view
    else:
        # Avoid profile `save()` recursion that can clash with deletes or migrations
        if hasattr(instance, 'profile'):
            # Guard against the profile already being removed from memory/state
            try:
                instance.profile.save()
            except UserProfile.DoesNotExist:
                pass


class Friendship(models.Model):
    user_from = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_requests')
    user_to = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_requests')
    status = models.CharField(max_length=20, choices=[
        ('pending', 'ממתין לאישור'), ('accepted', 'חברים'), ('blocked', 'חסום')
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user_from', 'user_to')


# ==========================================
# 1. Institutions and academic structure
# ==========================================

class University(models.Model):
    name = models.CharField(max_length=100, verbose_name="שם המוסד")
    logo = models.ImageField(upload_to='university_logos/', null=True, blank=True, verbose_name="לוגו המוסד", validators=[validate_file_size])
    brand_color = models.CharField(max_length=7, default='#0d6efd', verbose_name="צבע מותג")

    def __str__(self): return self.name

    def save(self, *args, **kwargs):
        if self.logo and not self.logo.name.endswith('.webp'):
            self.logo = compress_to_webp(self.logo)
        super().save(*args, **kwargs)


class Major(models.Model):
    university = models.ForeignKey(University, on_delete=models.CASCADE, verbose_name="אוניברסיטה")
    name = models.CharField(max_length=100, verbose_name="שם המקצוע")

    def __str__(self): return f"{self.name} - {self.university.name}"


class Course(models.Model):
    YEAR_CHOICES = [(1, 'שנה א\''), (2, 'שנה ב\''), (3, 'שנה ג\''), (4, 'שנה ד\''), (5, 'תואר שני')]
    SEMESTER_CHOICES = [('A', 'סמסטר א\''), ('B', 'סמסטר ב\''), ('summer', 'סמסטר קיץ'), ('yearly', 'שנתי')]

    major = models.ForeignKey(Major, on_delete=models.CASCADE, related_name='courses', null=True, blank=True,
                              verbose_name="מקצוע")
    name = models.CharField(max_length=150, verbose_name="שם הקורס")
    course_number = models.CharField(max_length=50, blank=True, verbose_name="מספר קורס")
    year = models.IntegerField(choices=YEAR_CHOICES, null=True, blank=True, verbose_name="שנת לימוד")
    semester = models.CharField(max_length=10, choices=SEMESTER_CHOICES, default='A', verbose_name="סמסטר")
    track = models.CharField(max_length=50, default='general', verbose_name="מסלול התמחות")
    description = models.TextField(blank=True, verbose_name="תיאור הקורס")
    view_count = models.PositiveIntegerField(default=0, verbose_name="מספר צפיות")
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_courses',
        verbose_name="יוצר הקורס"
    )

    def create_default_folder_tree(self):
        root_folders_names = ['הרצאות', 'תרגולים', 'מטלות', 'מבחני עבר', 'חומרי עזר נוספים']
        years = [str(y) for y in range(2020, 2027)]
        semesters = ['סמסטר א\'', 'סמסטר ב\'', 'סמסטר קיץ']

        for root_name in root_folders_names:
            root_folder, _ = Folder.objects.get_or_create(course=self, name=root_name, parent=None)
            if root_name != 'חומרי עזר נוספים':
                for year in years:
                    year_folder, _ = Folder.objects.get_or_create(course=self, name=year, parent=root_folder)
                    for sem in semesters:
                        Folder.objects.get_or_create(course=self, name=sem, parent=year_folder)

    def get_absolute_url(self):
        return reverse('course_detail', kwargs={'course_id': self.id})

    def __str__(self):
        return self.name


# ==========================================
# 2. File and folder management
# ==========================================

class Folder(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='folders')
    name = models.CharField(max_length=150, verbose_name="שם התיקייה")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subfolders')
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    color = models.CharField(max_length=10, default='#ffc107', verbose_name="צבע")
    staff_member = models.ForeignKey('AcademicStaff', on_delete=models.SET_NULL, null=True, blank=True,
                                     verbose_name="איש סגל")

    class Meta:
        unique_together = ('course', 'parent', 'name')

    def __str__(self): return self.name


class Document(models.Model):
    # Critical change: allow uploads without a course, for example from chat
    course = models.ForeignKey('Course', on_delete=models.CASCADE, null=True, blank=True)
    
    folder = models.ForeignKey('Folder', on_delete=models.CASCADE, null=True, blank=True, related_name='documents')
    title = models.CharField(max_length=200, verbose_name="כותרת הקובץ")

    # Attach the smart validator to the file field
    file = models.FileField(upload_to='documents/', validators=[validate_file_size, validate_file_type])
    file_content = models.TextField(blank=True, null=True, verbose_name="תוכן הקובץ לחיפוש")

    file_extension = models.CharField(max_length=10, blank=True)
    file_size_bytes = models.PositiveIntegerField(default=0)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    uploader_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name="כתובת IP של המעלה")
    staff_member = models.ForeignKey('AcademicStaff', on_delete=models.SET_NULL, null=True, blank=True,
                                     verbose_name="מרצה/מתרגל רלוונטי")
    upload_date = models.DateTimeField(auto_now_add=True)
    download_count = models.PositiveIntegerField(default=0)
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_documents', blank=True)

    # --- Personal tagging field ---
    personal_tag = models.CharField(
        max_length=20,
        choices=TAG_CHOICES,
        default='none',
        verbose_name="תיוג אישי"
    )
    def save(self, *args, **kwargs):
        # 1. פעולות קלילות ומהירות בלבד! (שליפת סיומת וגודל)
        if self.file:
            self.file_extension = os.path.splitext(self.file.name)[1].lower()
            try:
                self.file_size_bytes = self.file.size
            except:
                pass

        # 2. שומרים את הקובץ בבסיס הנתונים (לוקח שבריר שנייה)
        super().save(*args, **kwargs)

        # 3. קסם האסינכרוניות: שולחים את העבודה הכבדה ל-Celery
        # אנחנו מוודאים ש-update_fields ריק כדי שהשמירה ש-Celery עושה בעצמו בסוף
        # לא תפעיל את המשימה הזו שוב ושוב בלולאה אינסופית!
        if kwargs.get('update_fields') is None:
            from core.tasks import process_document_task
            from django.db import transaction
            # on_commit מבטיח שהמשימה תישלח לרקע *רק* אחרי שהמסמך נשמר סופית במסד הנתונים
            transaction.on_commit(lambda: process_document_task.delay(self.id))


    @property
    def total_likes(self):
        return self.likes.count()

    def get_absolute_url(self):
        return reverse('document_viewer', kwargs={'document_id': self.id})

    def __str__(self):
        return self.title

class ExternalResource(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='external_resources')
    title = models.CharField(max_length=255, verbose_name="כותרת")
    link = models.URLField(blank=True, null=True, verbose_name="קישור חיצוני")
    file = models.FileField(upload_to='external_resources/', blank=True, null=True, verbose_name="קובץ מקומי")
    created_at = models.DateTimeField(auto_now_add=True)

    # --- Personal tagging field ---
    personal_tag = models.CharField(
        max_length=20,
        choices=TAG_CHOICES,
        default='none',
        verbose_name="תיוג אישי"
    )

    def __str__(self):
        return self.title

# ==========================================
# 3.5 Document Audio (Read-aloud feature)
# ==========================================

class DocumentAudio(models.Model):
    """
    Stores generated audio files for documents to support read-aloud feature.
    Linked one-to-one to each Document for easy retrieval and playback.
    """
    document = models.OneToOneField('Document', on_delete=models.CASCADE, related_name='audio')
    audio_file = models.FileField(
        upload_to='audio_files/',
        null=True,
        blank=True,
        verbose_name="קובץ אודיו"
    )
    text_used = models.TextField(
        blank=True,
        null=True,
        verbose_name="טקסט שהשתמשנו בו",
        help_text="ערך התייחסות של 500 התווים הראשונים"
    )
    is_generated = models.BooleanField(
        default=False,
        verbose_name="האם נוצר בהצלחה"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="תאריך יצירה"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="תאריך עדכון"
    )

    class Meta:
        verbose_name = "אודיו מסמך"
        verbose_name_plural = "אודיו מסמכים"

    def __str__(self):
        return f"Audio for: {self.document.title}"

    def get_audio_url(self):
        """Return the URL to the audio file if it exists"""
        if self.audio_file:
            return self.audio_file.url
        return None

# ==========================================
# 4. Community system (social feed)
# ==========================================

class Community(models.Model):
    COMMUNITY_TYPES = [
        ('global', 'כלל ארצי'), ('university', 'אוניברסיטה'),
        ('major', 'מסלול לימודים'), ('year', 'שנתון ספציפי'), ('custom', 'קהילה חופשית (עתידי)')
    ]
    name = models.CharField(max_length=150, verbose_name="שם הקהילה")
    description = models.TextField(blank=True, verbose_name="תיאור")
    community_type = models.CharField(max_length=20, choices=COMMUNITY_TYPES, default='custom')
    university = models.ForeignKey(University, on_delete=models.CASCADE, null=True, blank=True)
    major = models.ForeignKey(Major, on_delete=models.CASCADE, null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    members = models.ManyToManyField(CustomUser, related_name='joined_communities', blank=True)

    def __str__(self): return self.name


class Post(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField(verbose_name="תוכן הפוסט")
    image = models.ImageField(upload_to='posts_images/', null=True, blank=True, validators=[validate_file_size])
    university = models.ForeignKey('University', on_delete=models.CASCADE, related_name='posts', null=True, blank=True)
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='posts', verbose_name="קהילה",
                                  null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(CustomUser, related_name='liked_posts', blank=True)

    @property
    def total_likes(self): return self.likes.count()

    class Meta: ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self.image and not self.image.name.endswith('.webp'):
            self.image = compress_to_webp(self.image)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('community_feed') + f'#post-{self.id}'


class MarketplacePost(Post):
    CATEGORY_CHOICES = [('rent', 'השכרת דירה'), ('sell', 'מכירה'), ('giveaway', 'מסירה')]
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='sell')


class VideoPost(Post):
    # Replace the heavy file field with a lightweight URL field
    youtube_url = models.URLField(
        max_length=500,
        verbose_name="קישור ליוטיוב",
        default='https://www.youtube.com',
        validators=[RegexValidator(
            regex=r'^(https?\:\/\/)?(www\.youtube\.com|youtu\.be)\/.+$',
            message='נא להזין קישור תקין מיוטיוב (למשל: https://www.youtube.com/watch?v=...)'
        )]
    )
    thumbnail = models.ImageField(upload_to='video_thumbnails/', null=True, blank=True, validators=[validate_file_size])

    @property
    def embed_url(self):
        """Convert a standard YouTube URL into an embeddable site URL."""
        url = self.youtube_url
        if not url:
            return ""

        # Handle regular YouTube watch URLs
        if 'youtube.com/watch?v=' in url:
            video_id = url.split('v=')[1].split('&')[0]
            return f"https://www.youtube.com/embed/{video_id}"

        # Handle shortened `youtu.be` links
        elif 'youtu.be/' in url:
            video_id = url.split('youtu.be/')[1].split('?')[0]
            return f"https://www.youtube.com/embed/{video_id}"

        return url

    def save(self, *args, **kwargs):
        if self.thumbnail and not self.thumbnail.name.endswith('.webp'):
            from .utils import compress_to_webp  # Extra safety to ensure the helper is available
            self.thumbnail = compress_to_webp(self.thumbnail)
        super().save(*args, **kwargs)


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    text = models.TextField(verbose_name="תגובה")
    created_at = models.DateTimeField(auto_now_add=True)

    def get_absolute_url(self):
        return self.post.get_absolute_url() + f'#comment-{self.id}'


# ==========================================
# 5. Academic staff, reports, and feedback
# ==========================================

class Report(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='reports')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    reason = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class AcademicStaff(models.Model):
    university = models.ForeignKey(University, on_delete=models.CASCADE, verbose_name="אוניברסיטה")
    name = models.CharField(max_length=100, verbose_name="שם מלא")
    email = models.EmailField(blank=True, null=True, verbose_name="אימייל (אופציונלי)")
    image = models.ImageField(upload_to='staff_images/', null=True, blank=True, verbose_name="תמונה", validators=[validate_file_size])
    average_rating = models.FloatField(default=0.0, verbose_name="דירוג ממוצע")
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
                                   verbose_name="הוסף על ידי")

    @property
    def privacy_name(self):
        parts = self.name.split()
        if len(parts) >= 2: return f"{parts[0][0]}. {' '.join(parts[1:])}"
        return self.name

    @property
    def total_reviews(self): return self.reviews.count()

    def __str__(self): return self.name

    def save(self, *args, **kwargs):
        if self.image and not self.image.name.endswith('.webp'):
            self.image = compress_to_webp(self.image)
        super().save(*args, **kwargs)


class Lecturer(AcademicStaff):
    title = models.CharField(max_length=50, default="מרצה", verbose_name="תואר")


class TeachingAssistant(AcademicStaff):
    title = models.CharField(max_length=50, default="מתרגל", verbose_name="תואר")


class StaffReview(models.Model):
    staff_member = models.ForeignKey(AcademicStaff, on_delete=models.CASCADE, related_name='reviews',
                                     verbose_name="איש סגל")
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="דירוג")
    review_text = models.TextField(verbose_name="חוות דעת")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('staff_member', 'user')
        ordering = ['-created_at']


class CourseSemesterStaff(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='semester_staff')
    staff_member = models.ForeignKey(AcademicStaff, on_delete=models.CASCADE)
    academic_year = models.IntegerField(verbose_name="שנה אקדמית")
    semester = models.CharField(max_length=10, choices=[('A', 'סמסטר א׳'), ('B', 'סמסטר ב׳'), ('summer', 'סמסטר קיץ')],
                                verbose_name="סמסטר")

    class Meta:
        unique_together = ('course', 'academic_year', 'semester', 'staff_member')

    def __str__(self):
        return f"{self.course.name} - {self.academic_year} {self.get_semester_display()}: {self.staff_member.name}"


class Feedback(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    screenshot = models.ImageField(upload_to='feedbacks/', null=True, blank=True, validators=[validate_file_size])
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False, verbose_name="טופל?")

    def save(self, *args, **kwargs):
        if self.screenshot and not self.screenshot.name.endswith('.webp'):
            self.screenshot = compress_to_webp(self.screenshot)
        super().save(*args, **kwargs)


# ==========================================
# 6. Automatic community creation
# ==========================================

@receiver(post_save, sender=UserProfile)
def auto_join_communities(sender, instance, created, **kwargs):
    if instance.university:
        uni_community, _ = Community.objects.get_or_create(
            name=f"קהילת {instance.university.name}",
            community_type='university',
            university=instance.university
        )
        uni_community.members.add(instance.user)

        if instance.major:
            major_community, _ = Community.objects.get_or_create(
                name=f"{instance.major.name} - {instance.university.name}",
                community_type='major',
                university=instance.university,
                major=instance.major
            )
            major_community.members.add(instance.user)

class DownloadLog(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    document = models.ForeignKey('Document', on_delete=models.CASCADE, related_name='downloads')
    # `auto_now_add=True` is the standard Django approach for creation timestamps
    download_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} הוריד את {self.document.title}"
class Vote(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    document = models.ForeignKey('Document', on_delete=models.CASCADE, related_name='votes')
    value = models.SmallIntegerField()  # `1` for like, `-1` for dislike
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'document')

    def __str__(self):
        return f"{self.user.username} - {self.value} on {self.document.title}"
# ==========================================
# 7. Notifications and automation
# ==========================================

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('friend_request', 'בקשת חברות'),
        ('system', 'התראת מערכת'),
        ('economy', 'פעולה כספית'),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='system')
    
    title = models.CharField(max_length=255, verbose_name="כותרת")
    message = models.TextField(verbose_name="הודעה")
    link = models.CharField(max_length=500, blank=True, null=True, verbose_name="קישור")
    
    # Generic relation for target object
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    is_read = models.BooleanField(default=False, verbose_name="נקרא?")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['user', 'is_read'])]

    def __str__(self):
        return f"התראה ל-{self.user.username}: {self.title}"


# --- New activity base and economy models ---
class BaseActivity(models.Model):
    """Abstract base model providing standard timestamps for activity models."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']


class CoinTransaction(BaseActivity):
    """Ledger of coin movements for users."""
    TX_TYPE_CHOICES = (
        ('signup', 'Signup'),
        ('referral', 'Referral'),
        ('quality_bonus', 'Quality bonus'),
        ('ai_summary', 'AI summary'),
        ('bounty', 'Bounty'),
        ('purchase', 'Purchase'),
        ('system', 'System'),
        ('spend', 'Spend'),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='coin_transactions')
    actor = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='granted_transactions', verbose_name="גורם מבצע")
    amount = models.IntegerField(verbose_name='amount')
    transaction_type = models.CharField(max_length=30, choices=TX_TYPE_CHOICES, default='system')
    description = models.CharField(max_length=500, blank=True, null=True)

    # Optional balance snapshots for auditing
    balance_before = models.IntegerField(null=True, blank=True)
    balance_after = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}: {self.amount} ({self.transaction_type})"


class ShopItem(BaseActivity):
    """A coin-based reward that users can redeem from the shop."""

    name = models.CharField(max_length=120, verbose_name="שם הפריט")
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    category = models.CharField(max_length=80, verbose_name="קטגוריה")
    description = models.TextField(blank=True, verbose_name="תיאור")
    price_coins = models.PositiveIntegerField(verbose_name="מחיר במטבעות")
    image = models.ImageField(upload_to='shop_items/', null=True, blank=True, verbose_name="תמונה")
    badge_label = models.CharField(max_length=40, blank=True, default='', verbose_name="תווית")
    redemption_code = models.CharField(max_length=120, blank=True, default='', verbose_name="קוד/שובר")
    redemption_instructions = models.TextField(blank=True, default='', verbose_name="הוראות מימוש")
    stock_quantity = models.PositiveIntegerField(null=True, blank=True, verbose_name="מלאי")
    is_featured = models.BooleanField(default=False, verbose_name="מוצג בראש החנות")
    is_active = models.BooleanField(default=True, verbose_name="פעיל")
    sort_order = models.PositiveIntegerField(default=0, verbose_name="סדר תצוגה")

    class Meta:
        ordering = ['sort_order', '-is_featured', 'price_coins', 'name']
        verbose_name = "פריט בחנות"
        verbose_name_plural = "פריטי חנות"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or f"shop-item-{uuid.uuid4().hex[:8]}"
            slug = base_slug
            suffix = 1
            while ShopItem.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                suffix += 1
                slug = f"{base_slug}-{suffix}"
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def is_limited_stock(self):
        return self.stock_quantity is not None

    @property
    def stock_label(self):
        if self.stock_quantity is None:
            return "מלאי פתוח"
        if self.stock_quantity == 0:
            return "אזל מהמלאי"
        return f"נותרו {self.stock_quantity}"

    def __str__(self):
        return f"{self.name} ({self.price_coins} 🪙)"


class ShopPurchase(BaseActivity):
    """Record of a shop redemption made by a user."""

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='shop_purchases')
    item = models.ForeignKey(ShopItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchases')
    item_name = models.CharField(max_length=120, verbose_name="שם פריט")
    category = models.CharField(max_length=80, verbose_name="קטגוריה")
    coins_spent = models.PositiveIntegerField(verbose_name="עלות במטבעות")
    delivery_code = models.CharField(max_length=120, blank=True, default='', verbose_name="קוד/שובר שנמסר")
    delivery_instructions = models.TextField(blank=True, default='', verbose_name="הוראות שנמסרו")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "רכישה מהחנות"
        verbose_name_plural = "רכישות חנות"

    def __str__(self):
        return f"{self.user.username} - {self.item_name}"

class UserCourseSelection(models.Model):
    """Link a user to a course and track whether the course is starred."""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='course_selections')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='selected_by_users')
    is_starred = models.BooleanField(default=False, verbose_name="מסומן בכוכב")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'course')  # Prevent duplicates

    def __str__(self):
        status = "⭐" if self.is_starred else "❌"
        return f"{self.user.username} - {self.course.name} {status}"

class ChatRoom(models.Model):
    participants = models.ManyToManyField(CustomUser, related_name='chat_rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100, blank=True, null=True, verbose_name="שם קבוצה (אופציונלי)")

    def __str__(self):
        return f"שיחה בין {', '.join([p.username for p in self.participants.all()])}"

class ChatMessage(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.TextField(blank=True)
    # Link to an existing file from the drive
    attached_file = models.ForeignKey('Document', on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']   


class DocumentComment(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='comments')
    # Use `settings.AUTH_USER_MODEL` instead of the concrete `User` class
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def get_absolute_url(self):
        return reverse('document_viewer', kwargs={'document_id': self.document.id}) + f'#comment-{self.id}'

    def __str__(self):
        # If your user model uses email instead of username, switch this to `self.user.email`
        return f"Comment by {self.user} on {self.document.title}"


# ==========================================
# 9. Analytics and Tracking
# ==========================================

class SearchLog(models.Model):
    """
    Tracks what users are searching for in the global search.
    Helps identify popular topics and "dead ends" (searches with 0 results).
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    search_query = models.CharField(max_length=255, verbose_name="מילת חיפוש")
    result_count = models.IntegerField(default=0, verbose_name="מספר תוצאות שנמצאו")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"חיפוש: '{self.search_query}' ({self.result_count} תוצאות)"


class AccountDeletionLog(models.Model):
    """
    Keeps a completely anonymous record of when a user deleted their account.
    Used purely for the Admin Analytics Dashboard to calculate churn rate.
    """
    deleted_at = models.DateTimeField(auto_now_add=True, verbose_name="תאריך מחיקה")
    reason = models.CharField(max_length=255, blank=True, null=True, verbose_name="סיבת עזיבה (אופציונלי)")

    # We do NOT save the username or email to respect privacy/GDPR after deletion.

    class Meta:
        ordering = ['-deleted_at']

    def __str__(self):
        return f"חשבון נמחק ב-{self.deleted_at.strftime('%Y-%m-%d')}"