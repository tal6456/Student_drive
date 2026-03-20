import os
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError


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
# פונקציית הגבלת העלאת קבצים של עד 20 מגה בייט
# ==============================================
def validate_file_size(value):
    """
    מוודא שקובץ שהועלה לא חורג מהמשקל המקסימלי המותר (20MB)
    """
    limit_mb = 20
    if value.size > limit_mb * 1024 * 1024:
        raise ValidationError(f"אופס! הקובץ גדול מדי ({limit_mb}MB מקסימום). כדי לשמור על האתר מהיר לכולם, אנא כווץ את הקובץ (ניתן לעשות זאת בחינם באתר iLovePDF) ונסה שוב.")