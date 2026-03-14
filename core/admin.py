from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import (University, Major, Course, Document, UserProfile,
                     Report, Lecturer, LecturerReview, CourseSemesterLecturer,
                     Feedback, Folder)


# ==========================================
# 1. מחלקות אב (ירושות) - הכוח האמיתי של הקוד
# ==========================================

class BaseAdmin(admin.ModelAdmin):
    """
    מחלקת אב לכל המודלים באדמין.
    כל מחלקה שתרש מפה תקבל אוטומטית את ההגדרות האלו.
    """
    list_per_page = 50  # מציג 50 פריטים בכל עמוד במקום 100 (טוען מהר יותר)
    empty_value_display = '- ריק -'  # מה להציג כשחסר מידע


class ModerationAdmin(BaseAdmin):
    """
    מחלקת אב למודלים שדורשים טיפול של מנהלים (דיווחים ופידבקים).
    היא יורשת מ-BaseAdmin ומוסיפה יכולות של סימון V מהיר ופעולות גורפות.
    """
    list_editable = ('is_resolved',)
    actions = ['mark_as_resolved']

    @admin.action(description='סמן פריטים נבחרים כטופלו (Resolved)')
    def mark_as_resolved(self, request, queryset):
        updated = queryset.update(is_resolved=True)
        self.message_user(request, f'{updated} פריטים עודכנו כטופלו בהצלחה.')


# ==========================================
# 2. מיזוג פרופיל הסטודנט לתוך מסך המשתמש (User)
# ==========================================
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'פרטי סטודנט מורחבים'
    fk_name = 'user'


class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_university')

    def get_university(self, instance):
        if hasattr(instance, 'profile') and instance.profile.university:
            return instance.profile.university.name
        return "לא הוגדר"

    get_university.short_description = 'מוסד לימודים'


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


# ==========================================
# 3. המודלים הרגילים (יורשים מ-BaseAdmin)
# ==========================================

@admin.register(University)
class UniversityAdmin(BaseAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Major)
class MajorAdmin(BaseAdmin):
    list_display = ('name', 'university')
    list_filter = ('university',)
    search_fields = ('name',)


@admin.register(Course)
class CourseAdmin(BaseAdmin):
    list_display = ('name', 'major', 'year', 'semester', 'view_count')
    list_filter = ('major', 'year', 'semester', 'track')
    search_fields = ('name', 'course_number')


@admin.register(Folder)
class FolderAdmin(BaseAdmin):
    list_display = ('name', 'course', 'parent', 'created_at')
    list_filter = ('course',)
    search_fields = ('name',)


@admin.register(Document)
class DocumentAdmin(BaseAdmin):
    list_display = ('title', 'course', 'folder', 'file_extension', 'uploaded_by', 'upload_date')
    list_filter = ('course', 'file_extension', 'is_anonymous', 'upload_date')
    search_fields = ('title', 'uploaded_by__username')  # חיפוש חכם גם לפי שם המעלה!
    date_hierarchy = 'upload_date'  # סרגל זמנים עליון לסינון מהיר


@admin.register(UserProfile)
class UserProfileAdmin(BaseAdmin):
    list_display = ('user', 'university', 'major', 'year', 'drive_coins')
    list_filter = ('university', 'year')
    search_fields = ('user__username', 'user__email')


@admin.register(Lecturer)
class LecturerAdmin(BaseAdmin):
    list_display = ('name', 'university')
    search_fields = ('name',)


@admin.register(LecturerReview)
class LecturerReviewAdmin(BaseAdmin):
    list_display = ('lecturer', 'user', 'rating', 'created_at')
    list_filter = ('rating',)


@admin.register(CourseSemesterLecturer)
class CourseSemesterLecturerAdmin(BaseAdmin):
    list_display = ('course', 'academic_year', 'semester', 'lecturer')
    list_filter = ('academic_year', 'semester')


# ==========================================
# 4. מודלי ניהול (יורשים מ-ModerationAdmin)
# ==========================================

@admin.register(Report)
class ReportAdmin(ModerationAdmin):  # יורש את פונקציות הטיפול!
    list_display = ('document', 'user', 'reason', 'is_resolved', 'created_at')
    list_filter = ('is_resolved', 'reason', 'created_at')
    search_fields = ('document__title', 'user__username')


@admin.register(Feedback)
class FeedbackAdmin(ModerationAdmin):  # יורש את פונקציות הטיפול!
    list_display = ('subject', 'user', 'is_resolved', 'created_at')
    list_filter = ('is_resolved', 'created_at')


# ==========================================
# 5. הגדרות מיתוג לאדמין
# ==========================================
admin.site.site_header = 'הדרייב הסטודנטיאלי - מערכת ניהול'
admin.site.site_title = 'ניהול הדרייב'
admin.site.index_title = 'לוח בקרה ראשי'