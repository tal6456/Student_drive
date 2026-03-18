from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# הבאנו לכאן את כל המודלים מהארכיטקטורה החדשה!
from .models import (
    CustomUser, UserProfile, Friendship,
    University, Major, Course, Folder, Document,
    Community, Post, MarketplacePost, VideoPost, Comment,
    AcademicStaff, Lecturer, TeachingAssistant, StaffReview, CourseSemesterStaff,
    Report, Feedback
)

# ==========================================
# 1. מחלקות אב (ירושות) - שומרים על הכוח שלך!
# ==========================================

class BaseAdmin(admin.ModelAdmin):
    """
    מחלקת אב לכל המודלים באדמין.
    כל מחלקה שתרש מפה תקבל אוטומטית את ההגדרות האלו.
    """
    list_per_page = 50
    empty_value_display = '- ריק -'


class ModerationAdmin(BaseAdmin):
    """
    מחלקת אב למודלים שדורשים טיפול של מנהלים (דיווחים ופידבקים).
    """
    list_editable = ('is_resolved',)
    actions = ['mark_as_resolved']

    @admin.action(description='סמן פריטים נבחרים כטופלו (Resolved)')
    def mark_as_resolved(self, request, queryset):
        updated = queryset.update(is_resolved=True)
        self.message_user(request, f'{updated} פריטים עודכנו כטופלו בהצלחה.')


# ==========================================
# 2. ניהול משתמשים (CustomUser + UserProfile)
# ==========================================

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'פרטי משתמש מורחבים'
    fk_name = 'user'


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')

    # הוספת שדה ה-role לעמוד העריכה והיצירה
    fieldsets = BaseUserAdmin.fieldsets + (
        ('הגדרות תפקיד במערכת (RBAC)', {'fields': ('role',)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('הגדרות תפקיד במערכת (RBAC)', {'fields': ('role',)}),
    )


@admin.register(UserProfile)
class UserProfileAdmin(BaseAdmin):
    list_display = ('user', 'university', 'major', 'year', 'lifetime_coins', 'current_balance')
    list_filter = ('university', 'year')
    search_fields = ('user__username', 'user__email')


@admin.register(Friendship)
class FriendshipAdmin(BaseAdmin):
    list_display = ('user_from', 'user_to', 'status', 'created_at')
    list_filter = ('status',)


# ==========================================
# 3. מוסדות, קורסים ותיקיות
# ==========================================

@admin.register(University)
class UniversityAdmin(BaseAdmin):
    list_display = ('name', 'brand_color')
    search_fields = ('name',)

@admin.register(Major)
class MajorAdmin(BaseAdmin):
    list_display = ('name', 'university')
    list_filter = ('university',)
    search_fields = ('name',)

@admin.register(Course)
class CourseAdmin(BaseAdmin):
    list_display = ('name', 'course_number', 'major', 'year', 'semester')
    list_filter = ('year', 'semester', 'major__university')
    search_fields = ('name', 'course_number')

@admin.register(Folder)
class FolderAdmin(BaseAdmin):
    list_display = ('name', 'course', 'parent', 'created_at')
    list_filter = ('course__major__university', 'created_at')
    search_fields = ('name', 'course__name')

@admin.register(Document)
class DocumentAdmin(BaseAdmin):
    list_display = ('title', 'course', 'folder', 'uploaded_by', 'upload_date')
    list_filter = ('course__major__university', 'upload_date')
    search_fields = ('title', 'course__name', 'uploaded_by__username')
    date_hierarchy = 'upload_date'


# ==========================================
# 4. קהילות ופוסטים
# ==========================================

@admin.register(Community)
class CommunityAdmin(BaseAdmin):
    list_display = ('name', 'community_type', 'university')
    list_filter = ('community_type', 'university')
    search_fields = ('name',)

@admin.register(Post)
class PostAdmin(BaseAdmin):
    list_display = ('user', 'community', 'university', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('content', 'user__username')

admin.site.register(MarketplacePost, BaseAdmin)
admin.site.register(VideoPost, BaseAdmin)
admin.site.register(Comment, BaseAdmin)


# ==========================================
# 5. סגל אקדמי ופידבקים
# ==========================================

@admin.register(AcademicStaff)
class AcademicStaffAdmin(BaseAdmin):
    list_display = ('name', 'university', 'average_rating')
    list_filter = ('university',)
    search_fields = ('name', 'email')

@admin.register(Lecturer)
class LecturerAdmin(BaseAdmin):
    list_display = ('name', 'university', 'title')
    list_filter = ('university',)
    search_fields = ('name',)

@admin.register(TeachingAssistant)
class TeachingAssistantAdmin(BaseAdmin):
    list_display = ('name', 'university', 'title')
    list_filter = ('university',)
    search_fields = ('name',)

@admin.register(StaffReview)
class StaffReviewAdmin(BaseAdmin):
    list_display = ('staff_member', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('staff_member__name', 'user__username')

@admin.register(CourseSemesterStaff)
class CourseSemesterStaffAdmin(BaseAdmin):
    list_display = ('course', 'staff_member', 'academic_year', 'semester')
    list_filter = ('academic_year', 'semester')

@admin.register(Report)
class ReportAdmin(ModerationAdmin):
    list_display = ('document', 'user', 'reason', 'is_resolved', 'created_at')
    list_filter = ('is_resolved', 'reason', 'created_at')
    search_fields = ('document__title', 'user__username')

@admin.register(Feedback)
class FeedbackAdmin(ModerationAdmin):
    list_display = ('subject', 'user', 'is_resolved', 'created_at')
    list_filter = ('is_resolved', 'created_at')


# ==========================================
# 6. הגדרות מיתוג לאדמין
# ==========================================
admin.site.site_header = 'הדרייב הסטודנטיאלי - מערכת ניהול'
admin.site.site_title = 'ניהול הדרייב'
admin.site.index_title = 'לוח בקרה ראשי'