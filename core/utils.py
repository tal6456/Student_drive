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
# 2. ולידטור משקל קבצים גלובלי (למודלים)
# ==============================================
def validate_file_size(value):
    """
    מוודא שקובץ שהועלה לא חורג מהמשקל המקסימלי שהוגדר למעלה
    """
    if value.size > GLOBAL_MAX_FILE_SIZE_MB * 1024 * 1024:
        raise ValidationError(f"אופס! הקובץ גדול מדי ({GLOBAL_MAX_FILE_SIZE_MB}MB מקסימום). כדי לשמור על האתר מהיר לכולם, אנא כווץ את הקובץ ונסה שוב.")