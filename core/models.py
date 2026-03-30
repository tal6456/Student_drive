from django.db import models, IntegrityError, transaction
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
import os
import random
import string
import uuid
from .utils import compress_to_webp, validate_file_size
from django.utils import timezone
from django.conf import settings
# ==========================================
# 0. מערכת המשתמשים (RBAC - Role Based Access Control)
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
def generate_referral_code():
    """מייצר קוד אקראי של אותיות ומספרים"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

class CustomUser(AbstractUser):
    """
    מודל המשתמש הראשי שמחליף את המודל הדיפולטיבי של ג'נגו.
    מנהל את ההתחברות ואת הרשאות המערכת.
    """
    ROLE_CHOICES = (
        ('member', 'חבר/ת קהילה'),  # סטודנטים, מרצים, משתמשים רגילים
        ('moderator', 'איש/אשת צוות'),  # מנהלים שכירים/מתנדבים
        ('admin', 'מנהל/ת העל'),  # אתה
    )

    username = models.CharField(
        max_length=150, unique=True, validators=[custom_username_validator],
        error_messages={'unique': "משתמש עם שם זה כבר קיים במערכת."},
    )

    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='member', verbose_name="תפקיד המשתמש")

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class UserProfile(models.Model):
    """
    פרופיל משתמש אחוד. גמיש מספיק כדי להכיל סטודנטים, מרצים ואנשים רגילים.
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')

    # --- מידע אקדמי (אופציונלי - רק למי שסטודנט) ---
    university = models.ForeignKey('University', on_delete=models.SET_NULL, null=True, blank=True,
                                   verbose_name="מוסד לימודים")
    major = models.ForeignKey('Major', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="מסלול לימודים")
    YEAR_CHOICES = [(1, 'שנה א\''), (2, 'שנה ב\''), (3, 'שנה ג\''), (4, 'שנה ד\''), (5, 'שנה ה\' / תואר שני')]
    year = models.IntegerField(choices=YEAR_CHOICES, null=True, blank=True, verbose_name="שנת לימוד")

    # --- פרטים אישיים ---
    bio = models.TextField(max_length=500, blank=True, verbose_name="קצת עלי (Bio)")
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True, verbose_name="תמונת פרופיל", validators=[validate_file_size])
    phone_number = models.CharField(max_length=15, blank=True, null=True, verbose_name="מספר טלפון")

    # --- כלכלת המערכת ומוניטין ---
    current_balance = models.PositiveIntegerField(default=0, verbose_name="יתרת מטבעות לשימוש")
    lifetime_coins = models.PositiveIntegerField(default=0, verbose_name="מוניטין (סך כל המטבעות שהורווחו מעשייה)")

    favorite_courses = models.ManyToManyField('Course', related_name='favorited_by_users', blank=True,
                                              verbose_name="קורסים מועדפים")

    # --- הגדרות משתמש ---
    THEME_CHOICES = [('light', 'יום (בהיר)'), ('dark', 'לילה (כהה)'), ('auto', 'אוטומטי')]
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

    # --- שדות שיתוף (Referrals) ---
    referral_code = models.CharField(max_length=12, unique=True, blank=True, null=True)
    referred_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='referrals')

    @property
    def rank_name(self):
        """ חישוב רמת המשתמש מבוסס אך ורק על המוניטין (Lifetime Coins) ולא על היתרה """
        if self.lifetime_coins >= 1000:
            return "💎 אלוף דרייב"
        elif self.lifetime_coins >= 500:
            return "🏆 אגדת סיכומים"
        elif self.lifetime_coins >= 200:
            return "🥇 עורך נאמן"
        elif self.lifetime_coins >= 50:
            return "🥈 תורם פעיל"
        return "🥉 מתלמד"

    # --- מתודות כלכלה חכמות ---
    def earn_coins(self, amount):
        """ הפעלה כאשר משתמש מרוויח מטבעות מעשייה (מעלה גם יתרה וגם מוניטין) """
        self.current_balance += amount
        self.lifetime_coins += amount
        self.save()

    def buy_coins(self, amount):
        """ הפעלה כאשר משתמש רוכש מטבעות בכסף (מעלה רק יתרה, המוניטין לא משתנה!) """
        self.current_balance += amount
        self.save()

    def spend_coins(self, amount):
        """ הפעלה כאשר משתמש מבזבז מטבעות (מוריד רק יתרה) """
        if self.current_balance >= amount:
            self.current_balance -= amount
            self.save()
            return True
        return False

    def __str__(self):
        return self.user.username

    def save(self, *args, **kwargs):
        # יצירת קוד הזמנה אם אין
        if not self.referral_code:
            self.referral_code = generate_referral_code()

        # --- כיווץ תמונת פרופיל ל-WebP ---
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
    """ מייצר פרופיל אוטומטית לכל משתמש חדש - גרסה בטוחה """
    if created:
        UserProfile.objects.create(user=instance)
    else:
        # משתמשים ב-filter.update כדי למנוע קריאה ל-save() של הפרופיל
        # שעלולה להתנגש עם תהליכי מחיקה או מיגרציות
        if hasattr(instance, 'profile'):
            # בדיקה שהפרופיל לא נמחק כבר מהזיכרון
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
# 1. מוסדות לימוד ותשתית אקדמית
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

    def __str__(self):
        return self.name


# ==========================================
# 2. ניהול קבצים ותיקיות
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
    course = models.ForeignKey('Course', on_delete=models.CASCADE)
    folder = models.ForeignKey('Folder', on_delete=models.CASCADE, null=True, blank=True, related_name='documents')
    title = models.CharField(max_length=200, verbose_name="כותרת הקובץ")

    # חיבור הוולידטור החכם לשדה הקובץ
    file = models.FileField(upload_to='documents/', validators=[]) # הוסף כאן את validate_file_size אם קיים

    file_extension = models.CharField(max_length=10, blank=True)
    file_size_bytes = models.PositiveIntegerField(default=0)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    staff_member = models.ForeignKey('AcademicStaff', on_delete=models.SET_NULL, null=True, blank=True,
                                     verbose_name="מרצה/מתרגל רלוונטי")
    upload_date = models.DateTimeField(auto_now_add=True)
    download_count = models.PositiveIntegerField(default=0)
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_documents', blank=True)

    # --- השדה החדש לתיוג אישי ---
    personal_tag = models.CharField(
        max_length=20,
        choices=TAG_CHOICES,
        default='none',
        verbose_name="תיוג אישי"
    )

    def save(self, *args, **kwargs):
        if self.file:
            self.file_extension = os.path.splitext(self.file.name)[1].lower()
            try:
                self.file_size_bytes = self.file.size
            except:
                pass

            # --- הלוגיקה החדשה: כיווץ תמונות שעולות לדרייב ---
            image_extensions = ['.jpg', '.jpeg', '.png']
            if self.file_extension in image_extensions and not self.file.name.endswith('.webp'):
                try:
                    # וודא שהפונקציה compress_to_webp מיובאת וקיימת
                    from .utils import compress_to_webp
                    self.file = compress_to_webp(self.file)
                    self.file_extension = '.webp'
                    self.file_size_bytes = self.file.size
                except:
                    pass

        super().save(*args, **kwargs)

    @property
    def total_likes(self):
        return self.likes.count()

    def __str__(self):
        return self.title


class ExternalResource(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='external_resources')
    title = models.CharField(max_length=255, verbose_name="כותרת")
    link = models.URLField(blank=True, null=True, verbose_name="קישור חיצוני")
    file = models.FileField(upload_to='external_resources/', blank=True, null=True, verbose_name="קובץ מקומי")
    created_at = models.DateTimeField(auto_now_add=True)

    # --- השדה החדש לתיוג אישי ---
    personal_tag = models.CharField(
        max_length=20,
        choices=TAG_CHOICES,
        default='none',
        verbose_name="תיוג אישי"
    )

    def __str__(self):
        return self.title
# ==========================================
# 4. מערכת הקהילה (הפיד החברתי)
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


class MarketplacePost(Post):
    CATEGORY_CHOICES = [('rent', 'השכרת דירה'), ('sell', 'מכירה'), ('giveaway', 'מסירה')]
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='sell')


class VideoPost(Post):
    # החלפנו את שדה הקובץ הכבד בשדה טקסט קליל לקישור בלבד!
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
        """ ממיר אוטומטית קישור רגיל של יוטיוב לקישור שניתן להציג באתר """
        url = self.youtube_url
        if not url:
            return ""

        # תופס קישורים רגילים של יוטיוב
        if 'youtube.com/watch?v=' in url:
            video_id = url.split('v=')[1].split('&')[0]
            return f"https://www.youtube.com/embed/{video_id}"

        # תופס קישורים מקוצרים (מהפלאפון)
        elif 'youtu.be/' in url:
            video_id = url.split('youtu.be/')[1].split('?')[0]
            return f"https://www.youtube.com/embed/{video_id}"

        return url

    def save(self, *args, **kwargs):
        if self.thumbnail and not self.thumbnail.name.endswith('.webp'):
            from .utils import compress_to_webp  # ליתר ביטחון נוודא שזה מיובא
            self.thumbnail = compress_to_webp(self.thumbnail)
        super().save(*args, **kwargs)


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    text = models.TextField(verbose_name="תגובה")
    created_at = models.DateTimeField(auto_now_add=True)


# ==========================================
# 5. סגל אקדמי, דיווחים ופידבק
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
# 6. יצירת קהילות אוטומטית
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
    document = models.ForeignKey('Document', on_delete=models.CASCADE)
    # שינוי: auto_now_add=True הוא הסטנדרט של דג'נגו לשדות תאריך יצירה
    download_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} הוריד את {self.document.title}"
class Vote(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    document = models.ForeignKey('Document', on_delete=models.CASCADE, related_name='votes')
    value = models.SmallIntegerField() # 1 ללייק, -1 לדיסלייק
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'document')

    def __str__(self):
        return f"{self.user.username} - {self.value} on {self.document.title}"
# ==========================================
#  רכיב הסוכן האישי כרגע מושבת. (Student Agent)
# ==========================================

# class AgentKnowledge(models.Model):
#     # משתמשים ב-CustomUser כי זה המודל שהגדרת למעלה
#     owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='agent_knowledge')
#     file = models.FileField(upload_to='agent_storage/', validators=[validate_file_size])
#     course_name = models.CharField(max_length=100, verbose_name="שיוך לקורס")
#
#     # שדה לאחסון הטקסט שחולץ מהקובץ כדי לחסוך עיבוד עתידי
#     extracted_text = models.TextField(blank=True, null=True, verbose_name="תוכן הטקסט שחולץ")
#
#     upload_date = models.DateTimeField(auto_now_add=True)
#
#     def __str__(self):
#         return f"Agent Knowledge: {self.course_name} ({self.owner.username})"

# ==========================================
# 8. מערכת התראות ואוטומציה (חדש)
# ==========================================

class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255, verbose_name="כותרת")
    message = models.TextField(verbose_name="הודעה")
    link = models.CharField(max_length=500, blank=True, null=True, verbose_name="קישור")
    is_read = models.BooleanField(default=False, verbose_name="נקרא?")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"התראה ל-{self.user.username}: {self.title}"


class UserCourseSelection(models.Model):
    """מודל שמחבר בין סטודנט לקורס ומסמן אם הוא במעקב (Star)"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='course_selections')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='selected_by_users')
    is_starred = models.BooleanField(default=False, verbose_name="מסומן בכוכב")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'course') # מונע כפילויות

    def __str__(self):
        status = "⭐" if self.is_starred else "❌"
        return f"{self.user.username} - {self.course.name} {status}"