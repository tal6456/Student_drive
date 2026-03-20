import os
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile


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