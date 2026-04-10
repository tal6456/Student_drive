"""
מה המטרה של הקובץ הזה
----------------------
הקובץ הזה מעצב ונותן יכולות לסופריוזר ולמנהלי האתר.
-----------
הקובץ מטפל ב:
1. אוטומיזציה וייצוא: הוספת אפשרות לייצוא כל טבלה לפורמט CSV בלחיצת כפתור.
2. ניהול קבצים ויזואלי: הצגת סוגי קבצים עם תוויות צבעוניות, הצגת גודל קובץ וקישורים ישירים.
3. ניהול משתמשים וכלכלה: חיבור הפרופיל למשתמש (Inline) ותצוגה של יתרת המטבעות (Coins).
4. מערכת בקרה (Moderation): ניהול דיווחים על קבצים פגומים ופידבקים ממשתמשים.
5. היררכיה אקדמית: שליטה על קורסים, מרצים ומוסדות לימוד.
"""

import csv
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.template.defaultfilters import filesizeformat
from django.http import HttpResponse

# ייבוא המודלים
from .models import (
    CustomUser, UserProfile, Friendship,
    University, Major, Course, Folder, Document,
    Community, Post, MarketplacePost, VideoPost, Comment,
    AcademicStaff, Lecturer, TeachingAssistant, StaffReview, CourseSemesterStaff,
    Report, Feedback,Notification, UserCourseSelection
)




# ==========================================
# 1. מחלקות אב (ירושות)
# ==========================================

class BaseAdmin(admin.ModelAdmin):
    list_per_page = 50
    empty_value_display = "- ריק -"
    actions = ['export_as_csv']

    @admin.action(description='📊 ייצא נתונים נבחרים ל-CSV')
    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename={meta}.csv'
        writer = csv.writer(response)
        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])
        return response


class ModerationAdmin(BaseAdmin):
    """עבור דיווחים ופידבקים"""
    list_editable = ('is_resolved',)
    actions = ['mark_as_resolved', 'export_as_csv']

    @admin.action(description='✅ סמן פריטים נבחרים כטופלו')
    def mark_as_resolved(self, request, queryset):
        queryset.update(is_resolved=True)
        self.message_user(request, "הפריטים עודכנו בהצלחה.")


# ==========================================
# 2. ניהול קבצים וסוכן ה-AI
# ==========================================

@admin.register(Document)
class DocumentAdmin(BaseAdmin):
    list_display = (
    'title_link', 'course', 'get_file_type', 'get_file_size', 'uploaded_by', 'download_count', 'upload_date')
    list_filter = ('course__major__university', 'upload_date')
    search_fields = ('title', 'course__name', 'uploaded_by__username')
    readonly_fields = ('download_count', 'upload_date')

    def title_link(self, obj):
        return format_html('<a href="{}" target="_blank" style="font-weight: bold; color: #1a73e8;">{} 🔗</a>',
                           obj.file.url, obj.title)

    title_link.short_description = 'שם הקובץ'

    def get_file_size(self, obj):
        try:
            return filesizeformat(obj.file.size)
        except:
            return "N/A"

    get_file_size.short_description = 'גודל'

    def get_file_type(self, obj):
        ext = obj.file.name.split('.')[-1].lower()
        colors = {'pdf': '#d32f2f', 'docx': '#1976d2', 'pptx': '#f57c00'}
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 10px;">{}</span>',
            colors.get(ext, '#757575'), ext.upper())

    get_file_type.short_description = 'סוג'


# @admin.register(AgentKnowledge)
# class AgentKnowledgeAdmin(BaseAdmin):
#     # שינינו את created_at ל-upload_date כדי שיתאים למודל
#     list_display = ('owner', 'course_name', 'get_text_stats', 'extraction_status', 'upload_date')
#     readonly_fields = ('extracted_text', 'upload_date')
#     search_fields = ('owner__username', 'course_name', 'extracted_text')
#
#     def get_text_stats(self, obj):
#         """מדד לכמה ידע ה-AI חילץ מהקובץ"""
#         if obj.extracted_text:
#             return f"{len(obj.extracted_text)} תווים"
#         return "ריק"
#     get_text_stats.short_description = 'נפח ידע'
#
#     def extraction_status(self, obj):
#         if obj.extracted_text and len(obj.extracted_text) > 10:
#             return format_html('<span style="color: green;">✔ עובד</span>')
#         return format_html('<span style="color: orange;">⏳ בהמתנה</span>')
#     extraction_status.short_description = 'סטטוס עיבוד'
#

# ==========================================
# 3. משתמשים וכלכלה
# ==========================================

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    fk_name = 'user'


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'role', 'is_staff', 'get_balance')

    def get_balance(self, obj):
        return f"{obj.profile.current_balance} 🪙"

    get_balance.short_description = 'יתרה'


@admin.register(UserProfile)
class UserProfileAdmin(BaseAdmin):
    list_display = ('user', 'university', 'lifetime_coins', 'current_balance')
    search_fields = ('user__username', 'referral_code')


# ==========================================
# 4. מוסדות, קורסים ותוכן
# ==========================================

@admin.register(Course)
class CourseAdmin(BaseAdmin):
    list_display = ('name', 'course_number', 'major', 'view_count')
    list_filter = ('major__university', 'year', 'semester')


@admin.register(Report)
class ReportAdmin(ModerationAdmin):
    list_display = ('document', 'user', 'reason', 'is_resolved', 'created_at')


@admin.register(Feedback)
class FeedbackAdmin(ModerationAdmin):
    list_display = ('subject', 'user', 'is_resolved', 'created_at')


# ==========================================
# 5. רישום שאר המודלים (בצורה בטוחה)
# ==========================================

# מודלים שמשתמשים ב-BaseAdmin ללא לוגיקה מיוחדת
admin.site.register([
    University, Major, Folder, Community, Post,
    MarketplacePost, VideoPost, Comment, Friendship,
    StaffReview, AcademicStaff, Lecturer, TeachingAssistant,
    CourseSemesterStaff,Notification, UserCourseSelection
], BaseAdmin)

# עיצוב כותרות
admin.site.site_header = 'הדרייב הסטודנטיאלי - מערכת ניהול'
admin.site.index_title = 'לוח בקרה אסטרטגי'

