from django.db import models
from django.contrib.auth.models import User


class University(models.Model):
    name = models.CharField(max_length=100, verbose_name="שם המוסד")

    def __str__(self): return self.name


class Major(models.Model):
    university = models.ForeignKey(University, on_delete=models.CASCADE, verbose_name="אוניברסיטה")
    name = models.CharField(max_length=100, verbose_name="שם המקצוע")

    def __str__(self): return f"{self.name} - {self.university.name}"


class Course(models.Model):
    YEAR_CHOICES = [(1, 'שנה א'), (2, 'שנה ב'), (3, 'שנה ג'), (4, 'שנה ד')]
    major = models.ForeignKey(Major, on_delete=models.CASCADE, related_name='courses', null=True, verbose_name="מקצוע")
    name = models.CharField(max_length=150, verbose_name="שם הקורס")
    course_number = models.CharField(max_length=50, blank=True, verbose_name="מספר קורס")
    year = models.IntegerField(choices=YEAR_CHOICES, null=True, blank=True, verbose_name="שנת לימוד")

    # שדה חדש לניתוח נתונים: כמה פעמים צפו בדף הקורס
    view_count = models.PositiveIntegerField(default=0, verbose_name="מספר צפיות")

    def __str__(self): return self.name


class Document(models.Model):
    CATEGORY_CHOICES = [('summary', 'סיכום'), ('exam', 'מבחן עבר'), ('hw', 'תרגיל בית'), ('other', 'אחר')]
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name="קורס")
    title = models.CharField(max_length=200, verbose_name="כותרת הקובץ")
    file = models.FileField(upload_to='documents/', verbose_name="קובץ")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name="סוג חומר")
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    upload_date = models.DateTimeField(auto_now_add=True)

    # שדה חדש לניתוח נתונים: כמה פעמים הורידו את הקובץ
    download_count = models.PositiveIntegerField(default=0, verbose_name="מספר הורדות")
    is_anonymous = models.BooleanField(default=False, verbose_name="העלה באופן אנונימי (הסתר את שמי)")

    def __str__(self): return self.title