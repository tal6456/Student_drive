"""
ארגז כלים ופונקציות עזר (Utility Functions)
==========================================

מה המטרה של הקובץ הזה?
----------------------
קובץ זה משמש כ"מרכז בקרה" טכני עבור האתר. הוא מרכז לוגיקה מורכבת שחוזרת על עצמה 
במקומות שונים, ובכך מבטיח אחידות בביצועים ובהגדרות האבטחה.

הקובץ מטפל ב-3 תחומים מרכזיים:
1. ניהול קבצים ותמונות: הגדרת הגבלות משקל (עד 20MB למסמך) וסוגי קבצים מותרים. 
   כולל מנגנון דחיסה אוטומטי ההופך תמונות לפורמט WebP כדי להאיץ את טעינת האתר.
2. אכיפת הרשאות מחיקה: מערכת חוקים חכמה שקובעת מי רשאי למחוק מה. 
   היא מגנה על תכנים קהילתיים (למשל: מניעת מחיקת תיקייה אם סטודנטים אחרים 
   כבר העלו אליה קבצים) ושומרת על זכויות היוצרים של המעלים.
3. תקינות נתונים (Validation): בדיקה אוטומטית של קבצים לפני שהם נשמרים 
   בשרת כדי למנוע העלאת קבצים כבדים מדי שעלולים להכביד על המערכת.

שינוי הגדרות בקובץ זה (כמו שינוי נפח קובץ מותר) ישפיע באופן מיידי על כל האתר.
---------------
יש להוסיף לפה פונקציונליות שחוזרת על עצמה במספר דפים באתר כדי שבלחיצת כפתור פה נשנה הכל.
"""

import os
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError

# ==============================================
# ⚙️ הגדרות גלובליות - "מרכז הבקרה" של הקבצים באתר
# ==============================================
GLOBAL_MAX_FILE_SIZE_MB = 20

GLOBAL_ALLOWED_DOCUMENTS = [
    '.pdf', '.doc', '.docx', '.txt',
    '.ppt', '.pptx', '.xls', '.xlsx',
    '.zip', '.rar'
]

GLOBAL_ALLOWED_IMAGES = [
    '.jpg', '.jpeg', '.png', '.webp', '.gif'
]

# ==============================================
# 1. פונקציית דחיסת תמונות (WebP)
# ==============================================
def compress_to_webp(image_field, max_size=(1200, 1200), quality=80):
    if not image_field:
        return image_field

    img = Image.open(image_field)

    if img.mode in ("RGBA", "P"):
        img = img.convert("RGBA")
    elif img.mode != "RGB":
        img = img.convert("RGB")

    img.thumbnail(max_size, Image.Resampling.LANCZOS)

    output = BytesIO()
    img.save(output, format='WEBP', quality=quality)
    output.seek(0)

    original_name = os.path.basename(image_field.name)
    new_filename = f"{os.path.splitext(original_name)[0]}.webp"

    return ContentFile(output.read(), name=new_filename)

# ==============================================
# 2. ולידטור משקל קבצים חכם (שומרים על השם המקורי!)
# ==============================================
def validate_file_size(value):
    ext = os.path.splitext(value.name)[1].lower()
    image_exts = ['.jpg', '.jpeg', '.png', '.webp']

    if ext in image_exts:
        limit = 5 * 1024 * 1024  # תמונות עד 5MB
        if value.size > limit:
            raise ValidationError('תמונות מוגבלות לגודל של עד 5MB.')
    else:
        limit = 20 * 1024 * 1024  # מסמכים עד 20MB
        if value.size > limit:
            raise ValidationError('מסמכים מוגבלים לגודל של עד 20MB.')

# ==============================================
# 3. מוח ההרשאות - מערכת מחיקות חכמה
# ==============================================
def check_deletion_permission(user, obj, obj_type):
    """
    בודק האם למשתמש יש הרשאה למחוק את האובייקט הספציפי.
    מחזיר טאפל: (True/False, "הודעת שגיאה במידת הצורך")
    """
    # 1. מנהלי מערכת יכולים למחוק הכל, תמיד.
    if user.is_superuser or user.is_staff or getattr(user, 'role', '') in ['admin', 'moderator']:
        return True, ""

    # 2. חוקי מסמכים
    if obj_type == 'document':
        if getattr(obj, 'uploaded_by', None) == user:
            return True, ""
        return False, "אין לך הרשאה למחוק קובץ זה, מכיוון שמשתמש אחר העלה אותו."

    # 3. חוקי פוסטים ותגובות (בפיד הקהילה)
    elif obj_type in ['post', 'comment']:
        if getattr(obj, 'user', None) == user:
            return True, ""
        return False, "אין לך הרשאה למחוק פריט זה."

    # 4. חוקי תיקיות (הגנת קהילה מורחבת)
    elif obj_type == 'folder':
        # קודם כל, האם הסטודנט הזה בכלל יצר את התיקייה?
        if getattr(obj, 'created_by', None) != user:
            return False, "ניתן למחוק רק תיקיות שאתה יצרת בעצמך."

        # הגנת תוכן: האם משתמשים אחרים העלו מסמכים לתיקייה הזו?
        has_others_docs = obj.documents.exclude(uploaded_by=user).exists()
        if has_others_docs:
            return False, "לא ניתן למחוק את התיקייה מכיוון שסטודנטים אחרים כבר הוסיפו אליה חומרי לימוד."

        # הגנת תוכן 2: האם משתמשים אחרים יצרו תתי-תיקיות בתוך התיקייה הזו?
        has_others_folders = obj.subfolders.exclude(created_by=user).exists()
        if has_others_folders:
            return False, "לא ניתן למחוק את התיקייה מכיוון שסטודנטים אחרים פתחו בתוכה תתי-תיקיות."

        return True, ""

    return False, "סוג אובייקט לא מוכר למערכת המחיקות."