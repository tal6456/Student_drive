"""
What is this file for?
----------------------
This file shapes the Django admin experience and adds capabilities for the
superuser and site managers.

It handles:
1. Automation and export: adds one-click CSV export for admin tables.
2. Visual file management: shows file types with colored labels, file sizes,
   and direct links.
3. User and economy management: connects the profile inline to the user and
   displays coin balances.
4. Moderation: manages broken-file reports and user feedback.
5. Academic hierarchy: controls courses, lecturers, and institutions.
"""

import csv
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.template.defaultfilters import filesizeformat
from django.http import HttpResponse
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount
from django.contrib import messages
from .utils import process_transaction

# Quality bonus default for admin grants
QUALITY_BONUS_AMOUNT = 10

# Import the models
from .models import (
    CustomUser, UserProfile, Friendship,
    University, Major, Course, Folder, Document,
    Community, Post, MarketplacePost, VideoPost, Comment,DocumentComment,
    AcademicStaff, Lecturer, TeachingAssistant, StaffReview, CourseSemesterStaff,
    Report, Feedback,Notification, UserCourseSelection,
    CoinTransaction, ShopItem, ShopPurchase
)




# ==========================================
# 1. Base admin classes
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
    """Shared admin behavior for reports and feedback."""
    list_editable = ('is_resolved',)
    actions = ['mark_as_resolved', 'export_as_csv']

    @admin.action(description='✅ סמן פריטים נבחרים כטופלו')
    def mark_as_resolved(self, request, queryset):
        queryset.update(is_resolved=True)
        self.message_user(request, "הפריטים עודכנו בהצלחה.")


# ==========================================
# 2. File management
# ==========================================

@admin.register(Document)
class DocumentAdmin(BaseAdmin):
    list_display = (
    'title_link', 'course', 'get_file_type', 'get_file_size', 'uploaded_by','uploader_ip', 'download_count', 'upload_date')
    list_filter = ('course__major__university', 'upload_date')
    search_fields = ('title', 'course__name', 'uploaded_by__username', 'uploader_ip')
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

    @admin.action(description='🎖️ הענק בונוס איכות (10 מטבעות) למעלות המסמכים הנבחרים')
    def grant_quality_bonus(self, request, queryset):
        successes = 0
        failures = []
        bonus_amount = QUALITY_BONUS_AMOUNT
        for doc in queryset:
            if not doc.uploaded_by:
                failures.append((doc.pk, 'No uploader'))
                continue
            try:
                process_transaction(
                    doc.uploaded_by,
                    bonus_amount,
                    tx_type='quality_bonus',
                    description=f'Quality bonus for "{doc.title}"',
                    actor=request.user,
                    bonus_increases_lifetime=True,
                )
                successes += 1
            except Exception as e:
                failures.append((doc.pk, str(e)))

        msg = f"בונוס הוענק ל-{successes} מסמכים."
        if failures:
            msg += f" כשלונות: {len(failures)}"
            self.message_user(request, msg, level=messages.WARNING)
        else:
            self.message_user(request, msg, level=messages.SUCCESS)

    actions = ['grant_quality_bonus']


# ==========================================
# 3. Users and economy
# ==========================================

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    fk_name = 'user'

@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    
    # 1. עדכון רשימת התצוגה כך שתכלול את הפונקציות החדשות
    list_display = ('username', 'email', 'role', 'is_staff', 'get_balance', 'is_email_verified', 'login_method', 'last_ip')

    # פונקציה ששולפת את ה-IP מהמסמך האחרון שהיוזר העלה
    def last_ip(self, obj):
        last_doc = Document.objects.filter(uploaded_by=obj).order_by('-upload_date').first()
        return last_doc.uploader_ip if last_doc else "אין העלאות"

    last_ip.short_description = 'IP אחרון (מהעלאה)'

    def get_balance(self, obj):
        return f"{obj.profile.current_balance} 🪙"
    get_balance.short_description = 'יתרה'

    # -------------------------------------------------------------
    # פונקציה לבדיקה האם המייל אומת (מציג אייקון וי/איקס)
    # -------------------------------------------------------------
    def is_email_verified(self, obj):
        return EmailAddress.objects.filter(user=obj, verified=True).exists()
    
    is_email_verified.boolean = True  # הופך את זה לאייקון גרפי נחמד
    is_email_verified.short_description = 'מייל מאומת'

    # -------------------------------------------------------------
    # פונקציה להצגת שיטת ההתחברות (גוגל או רגיל)
    # -------------------------------------------------------------
    def login_method(self, obj):
        social_accounts = SocialAccount.objects.filter(user=obj)
        if social_accounts.exists():
            providers = [acc.provider.capitalize() for acc in social_accounts]
            return ", ".join(providers)
        return 'מייל וסיסמה'
    
    login_method.short_description = 'שיטת התחברות'

@admin.register(UserProfile)
class UserProfileAdmin(BaseAdmin):
    list_display = ('user', 'university', 'lifetime_coins', 'current_balance')
    search_fields = ('user__username', 'referral_code', 'user__email')
    readonly_fields = ('referral_code',)


# ==========================================
# 4. Institutions, courses, and content
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
# 5. Register the remaining models safely
# ==========================================

# Models that use `BaseAdmin` without special logic
admin.site.register([
    University, Major, Folder, Community, Post,
    MarketplacePost, VideoPost, Comment, Friendship,DocumentComment,
    StaffReview, AcademicStaff, Lecturer, TeachingAssistant,
    CourseSemesterStaff, UserCourseSelection
], BaseAdmin)


@admin.register(Notification)
class NotificationAdmin(BaseAdmin):
    list_display = ('user', 'notification_type', 'title', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'title', 'message')


@admin.register(CoinTransaction)
class CoinTransactionAdmin(BaseAdmin):
    list_display = ('user', 'colored_amount', 'transaction_type', 'balance_after', 'created_at')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('user__username', 'description')

    def colored_amount(self, obj):
        color = 'green' if obj.amount > 0 else 'red'
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.amount)

    colored_amount.short_description = 'סכום'


@admin.register(ShopItem)
class ShopItemAdmin(BaseAdmin):
    list_display = ('name', 'category', 'price_coins', 'stock_quantity', 'is_featured', 'is_active', 'sort_order', 'created_at')
    list_filter = ('category', 'is_featured', 'is_active', 'created_at')
    search_fields = ('name', 'category', 'description', 'redemption_code')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(ShopPurchase)
class ShopPurchaseAdmin(BaseAdmin):
    list_display = ('user', 'item_name', 'coins_spent', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('user__username', 'item_name', 'delivery_code')
# Admin site titles
admin.site.site_header = 'הדרייב הסטודנטיאלי - מערכת ניהול'
admin.site.index_title = 'לוח בקרה אסטרטגי'

