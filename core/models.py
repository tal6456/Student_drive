from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator, MaxValueValidator
import datetime
import os
import random
import string

from django.contrib.auth.models import User
from django.core.validators import RegexValidator

# מעקף חוקי: משנה את חוקי האבטחה של ג'נגו כך שיאפשרו רווחים בשם המשתמש
custom_username_validator = RegexValidator(
    regex=r'^[\w.@+\- ]+$',  # הוספנו רווח לתוך הביטוי הרגולרי!
    message='שם משתמש יכול להכיל אותיות, מספרים, רווחים, ותווים מיוחדים (@/./+/-/_).'
)
# דורסים את החוקים המקוריים של המודל
User._meta.get_field('username').validators = [custom_username_validator]

# ==========================================
# 1. מוסדות לימוד ותשתית אקדמית
# ==========================================

class University(models.Model):
    name = models.CharField(max_length=100, verbose_name="שם המוסד")
    logo = models.ImageField(upload_to='university_logos/', null=True, blank=True, verbose_name="לוגו המוסד")
    brand_color = models.CharField(max_length=7, default='#0d6efd', verbose_name="צבע מותג")

    def __str__(self): return self.name


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
        """
        מתודה מרכזית ליצירת עץ התיקיות.
        מונעת כפילויות על ידי בדיקת .exists() לפני כל יצירה.
        """
        root_folders_names = ['הרצאות', 'תרגולים', 'מטלות', 'מבחני עבר', 'חומרי עזר נוספים']
        years = [str(y) for y in range(2020, 2027)]
        semesters = ['סמסטר א\'', 'סמסטר ב\'', 'סמסטר קיץ']

        for root_name in root_folders_names:
            # שימוש ב-get_or_create מונע כפילות ברמת ה-Root
            root_folder, _ = Folder.objects.get_or_create(
                course=self,
                name=root_name,
                parent=None
            )

            if root_name != 'חומרי עזר נוספים':
                for year in years:
                    year_folder, _ = Folder.objects.get_or_create(
                        course=self,
                        name=year,
                        parent=root_folder
                    )

                    for sem in semesters:
                        Folder.objects.get_or_create(
                            course=self,
                            name=sem,
                            parent=year_folder
                        )
    def __str__(self): return self.name


# ==========================================
# 2. ניהול קבצים ותיקיות
# ==========================================

class Folder(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='folders')
    name = models.CharField(max_length=150, verbose_name="שם התיקייה")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subfolders')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    color = models.CharField(max_length=10, default='#ffc107', verbose_name="צבע")
    # הקישור תוקן לסגל אקדמי כללי
    staff_member = models.ForeignKey('AcademicStaff', on_delete=models.SET_NULL, null=True, blank=True,
                                     verbose_name="איש סגל")

    class Meta:
        unique_together = ('course', 'parent', 'name')

    def __str__(self): return self.name


class Document(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, null=True, blank=True, related_name='documents')
    title = models.CharField(max_length=200, verbose_name="כותרת הקובץ")
    file = models.FileField(upload_to='documents/')
    file_extension = models.CharField(max_length=10, blank=True)
    file_size_bytes = models.PositiveIntegerField(default=0)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    # הקישור תוקן לסגל אקדמי כללי
    staff_member = models.ForeignKey('AcademicStaff', on_delete=models.SET_NULL, null=True, blank=True,
                                     verbose_name="מרצה/מתרגל רלוונטי")

    upload_date = models.DateTimeField(auto_now_add=True)
    download_count = models.PositiveIntegerField(default=0)
    is_anonymous = models.BooleanField(default=False)
    likes = models.ManyToManyField(User, related_name='liked_documents', blank=True)

    def save(self, *args, **kwargs):
        if self.file:
            self.file_extension = os.path.splitext(self.file.name)[1].lower()
            try:
                self.file_size_bytes = self.file.size
            except:
                pass
        super().save(*args, **kwargs)

    @property
    def total_likes(self):
        return self.likes.count()

    def __str__(self):
        return self.title


# ==========================================
# 3. פרופיל משתמש ומערכת חברים
# ==========================================
# פונקציית עזר לייצור קוד רנדומלי
def generate_referral_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    university = models.ForeignKey(University, on_delete=models.SET_NULL, null=True, blank=True)
    major = models.ForeignKey(Major, on_delete=models.SET_NULL, null=True, blank=True)
    YEAR_CHOICES = [(1, 'שנה א\''), (2, 'שנה ב\''), (3, 'שנה ג\''), (4, 'שנה ד\''), (5, 'שנה ה\' / תואר שני')]
    year = models.IntegerField(choices=YEAR_CHOICES, null=True, blank=True, verbose_name="שנת לימוד")
    bio = models.TextField(max_length=500, blank=True, verbose_name="קצת עלי (Bio)")
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True, verbose_name="מספר טלפון")
    drive_coins = models.PositiveIntegerField(default=0)
    # הקורסים המועדפים של המשתמש (לגישה מהירה)
    favorite_courses = models.ManyToManyField(Course, related_name='favorited_by', blank=True,
                                              verbose_name="קורסים מועדפים")

    # הגדרות משתמש
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
    show_coins_publicly = models.BooleanField(default=True)
    default_anonymous_upload = models.BooleanField(default=False, verbose_name="העלה קבצים באופן אנונימי כברירת מחדל")

    # שדות השיתוף
    referral_code = models.CharField(max_length=12, unique=True, blank=True, null=True)
    referred_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')

    @property
    def rank_name(self):
        if self.drive_coins >= 500:
            return "🏆 אגדת סיכומים"
        elif self.drive_coins >= 200:
            return "🥇 מתרגל בכיר"
        return "🥉 סטודנט"

    def __str__(self):
        return self.user.username

    def save(self, *args, **kwargs):
        # מייצר קוד רק אם אין כזה (בזמן יצירה ראשונית)
        if not self.referral_code:
            self.referral_code = generate_referral_code()
        super().save(*args, **kwargs)

    @property
    def pending_friend_requests(self):
        # מחזיר את כל בקשות החברות שהמשתמש קיבל ועדיין ממתינות לאישור
        return self.user.received_requests.filter(status='pending')

    @property
    def get_accepted_friends(self):
        """מחזיר רשימה של כל המשתמשים שהם חברים מאושרים שלי"""
        from django.db import models
        from .models import Friendship

        # מושך את כל קשרי החברות המאושרים שאני חלק מהם
        relations = Friendship.objects.filter(
            (models.Q(user_from=self.user) | models.Q(user_to=self.user)),
            status='accepted'
        )

        # מוציא מתוך הקשרים את המשתמשים עצמם (שהם לא אני)
        friends = []
        for rel in relations:
            if rel.user_from == self.user:
                friends.append(rel.user_to)
            else:
                friends.append(rel.user_from)
        return friends


@receiver(post_save, sender=User)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    if created: UserProfile.objects.create(user=instance)
    instance.profile.save()


class Friendship(models.Model):
    """ ניהול רשת החברים (בקשות חברות ואישורן) """
    user_from = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_requests')
    user_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    status = models.CharField(max_length=20, choices=[
        ('pending', 'ממתין לאישור'),
        ('accepted', 'חברים'),
        ('blocked', 'חסום')
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user_from', 'user_to')


# ==========================================
# 4. מערכת הקהילה (הפיד החברתי)
# ==========================================

class Post(models.Model):
    """
    מודל האב של הפוסטים.
    כל פוסט ברשת החברתית יתחיל כאן.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField(verbose_name="תוכן הפוסט")
    image = models.ImageField(upload_to='posts_images/', null=True, blank=True)

    # שיוך לקהילה - מאפשר לנו לסנן פוסטים לפי המוסד/מקצוע של הסטודנט
    university = models.ForeignKey(University, on_delete=models.CASCADE)
    major = models.ForeignKey(Major, on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)

    @property
    def total_likes(self):
        """מחזיר את כמות הלייקים שיש לפוסט"""
        return self.likes.count()

    class Meta:
        ordering = ['-created_at']  # הכי חדש מופיע למעלה


class MarketplacePost(Post):
    """
    ירושת מודלים: פוסט של לוח מודעות.
    הוא מקבל את כל השדות של Post ומוסיף מחיר וקטגוריה.
    """
    CATEGORY_CHOICES = [
        ('rent', 'השכרת דירה'),
        ('sell', 'מכירה'),
        ('giveaway', 'מסירה'),
    ]
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='sell')


class VideoPost(Post):
    """ ירושת מודלים: פוסט שמכיל סרטון """
    video_file = models.FileField(upload_to='posts_videos/')
    thumbnail = models.ImageField(upload_to='video_thumbnails/', null=True, blank=True)


class Comment(models.Model):
    """ תגובות לפוסטים """
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField(verbose_name="תגובה")
    created_at = models.DateTimeField(auto_now_add=True)


# ==========================================
# 5. סגל אקדמי, דיווחים ופידבק
# ==========================================

class Report(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='reports')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class AcademicStaff(models.Model):
    """
    מודל אב מוחשי - אליו אנחנו מקשרים מסמכים, תיקיות וביקורות.
    """
    university = models.ForeignKey(University, on_delete=models.CASCADE, verbose_name="אוניברסיטה")
    name = models.CharField(max_length=100, verbose_name="שם מלא")
    email = models.EmailField(blank=True, null=True, verbose_name="אימייל (אופציונלי)")
    image = models.ImageField(upload_to='staff_images/', null=True, blank=True, verbose_name="תמונה")

    # --- השורה החדשה שהוספנו ---
    # הופך את המאפיין לשדה אמיתי כדי שנוכל למיין לפי דירוג ב-SQL
    average_rating = models.FloatField(default=0.0, verbose_name="דירוג ממוצע")

    @property
    def privacy_name(self):
        """פונקציה לשמירת פרטיות: מציגה אות ראשונה ושם משפחה מלא."""
        parts = self.name.split()
        if len(parts) >= 2:
            first_initial = parts[0][0]
            last_name = " ".join(parts[1:])
            return f"{first_initial}. {last_name}"
        return self.name

    @property
    def total_reviews(self):
        return self.reviews.count()

    def __str__(self):
        return self.name


class Lecturer(AcademicStaff):
    """מודל מרצה - יורש מסגל אקדמי"""
    title = models.CharField(max_length=50, default="מרצה", verbose_name="תואר")


class TeachingAssistant(AcademicStaff):
    """מודל מתרגל - יורש מסגל אקדמי"""
    title = models.CharField(max_length=50, default="מתרגל", verbose_name="תואר")


class StaffReview(models.Model):
    """ ביקורות לכל סוגי הסגל האקדמי """
    staff_member = models.ForeignKey(AcademicStaff, on_delete=models.CASCADE, related_name='reviews', verbose_name="איש סגל")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="דירוג")
    review_text = models.TextField(verbose_name="חוות דעת")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('staff_member', 'user') # משתמש לא יכול לדרג פעמיים את אותו אדם
        ordering = ['-created_at']


class CourseSemesterStaff(models.Model):
    """ שיוך של איש סגל (מרצה או מתרגל) לקורס בסמסטר מסוים """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='semester_staff')
    staff_member = models.ForeignKey(AcademicStaff, on_delete=models.CASCADE)
    academic_year = models.IntegerField(verbose_name="שנה אקדמית")
    semester = models.CharField(max_length=10, choices=[('A', 'סמסטר א׳'), ('B', 'סמסטר ב׳'), ('summer', 'סמסטר קיץ')], verbose_name="סמסטר")

    class Meta:
        unique_together = ('course', 'academic_year', 'semester', 'staff_member')

    def __str__(self):
        return f"{self.course.name} - {self.academic_year} {self.get_semester_display()}: {self.staff_member.name}"


class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    screenshot = models.ImageField(upload_to='feedbacks/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False, verbose_name="טופל?")

# ==========================================
# 6. אוטומיזציה (סיגנלים ליצירת תיקיות)
# ==========================================

@receiver(post_save, sender=Course)
def create_course_folder_structure(sender, instance, created, **kwargs):
    """
    סיגנל שמופעל אוטומטית בכל פעם שקורס חדש נוצר במסד הנתונים.
    הוא בונה עץ תיקיות מלא: קטגוריות ראשיות -> שנים -> סמסטרים.
    """
    if created:
        # 1. הגדרת התיקיות הראשיות
        root_folders_names = [
            'הרצאות',
            'תרגולים',
            'מטלות',
            'מבחני עבר',
            'חומרי עזר נוספים'
        ]

        # 2. הגדרת השנים והסמסטרים
        years_list = [str(y) for y in range(2026, 2019, -1)] # יוצר: 2026, 2025... 2020
        semesters = ['סמסטר א\'', 'סמסטר ב\'', 'סמסטר קיץ']

        # 3. בניית העץ
        for root_name in root_folders_names:
            # יצירת תיקיית האב (Root)
            root_folder = Folder.objects.create(
                name=root_name,
                course=instance,
                parent=None
            )

            # אם זו לא תיקיית "חומרי עזר נוספים", ניצור לה את מבנה השנים והסמסטרים
            if root_name != 'חומרי עזר נוספים':
                for year in years_list:
                    # יצירת תיקיית השנה בתוך התיקייה הראשית
                    year_folder = Folder.objects.create(
                        name=year,
                        course=instance,
                        parent=root_folder
                    )

                    # יצירת תיקיות הסמסטרים בתוך תיקיית השנה
                    for semester in semesters:
                        Folder.objects.create(
                            name=semester,
                            course=instance,
                            parent=year_folder
                        )

# @receiver(post_save, sender=Course)
# def auto_create_course_folders(sender, instance, created, **kwargs):
#     if created:
#         instance.create_default_folder_tree()