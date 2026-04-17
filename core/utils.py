"""
Utility toolbox and shared helpers
==================================

What is this file for?
----------------------
This file serves as a technical control center for the site. It collects
shared logic that appears in multiple places, helping keep behavior and
security consistent.

It covers three main areas:
1. File and image handling: defines file-size limits and allowed types,
   and includes automatic image compression to WebP for faster loading.
2. Deletion permissions: applies a smart rule set that decides who may
   delete what, including protections for community-owned content.
3. Validation: checks files before they are stored so oversized uploads
   do not overload the system.

Changing settings in this file, such as the max allowed file size, affects
the entire site immediately.
"""

import os
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError

# ==============================================
# Global settings: the shared control center for site file handling
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
# 1. Image compression helper (WebP)
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
# 2. Smart file-size validator that preserves the original filename
# ==============================================
def validate_file_size(value):
    ext = os.path.splitext(value.name)[1].lower()
    image_exts = ['.jpg', '.jpeg', '.png', '.webp']

    if ext in image_exts:
        limit = 5 * 1024 * 1024  # Images up to 5 MB
        if value.size > limit:
            raise ValidationError('תמונות מוגבלות לגודל של עד 5MB.')
    else:
        limit = 20 * 1024 * 1024  # Documents up to 20 MB
        if value.size > limit:
            raise ValidationError('מסמכים מוגבלים לגודל של עד 20MB.')

# ==============================================
# 3. Permission engine: smart deletion rules
# ==============================================
def check_deletion_permission(user, obj, obj_type):
    """
    Check whether the given user may delete the specific object.
    Returns a tuple: `(True/False, "error message if needed")`.
    """
    # 1. System admins can always delete everything
    if user.is_superuser or user.is_staff or getattr(user, 'role', '') in ['admin', 'moderator']:
        return True, ""

    # 2. Document rules
    if obj_type == 'document':
        if getattr(obj, 'uploaded_by', None) == user:
            return True, ""
        return False, "אין לך הרשאה למחוק קובץ זה, מכיוון שמשתמש אחר העלה אותו."

    # 3. Post and comment rules in the community feed
    elif obj_type in ['post', 'comment']:
        if getattr(obj, 'user', None) == user:
            return True, ""
        return False, "אין לך הרשאה למחוק פריט זה."

    # 4. Folder rules with stronger community protection
    elif obj_type == 'folder':
        # First, did this user create the folder at all?
        if getattr(obj, 'created_by', None) != user:
            return False, "ניתן למחוק רק תיקיות שאתה יצרת בעצמך."

        # Content protection: did other users upload documents into this folder?
        has_others_docs = obj.documents.exclude(uploaded_by=user).exists()
        if has_others_docs:
            return False, "לא ניתן למחוק את התיקייה מכיוון שסטודנטים אחרים כבר הוסיפו אליה חומרי לימוד."

        # Content protection 2: did other users create subfolders under this folder?
        has_others_folders = obj.subfolders.exclude(created_by=user).exists()
        if has_others_folders:
            return False, "לא ניתן למחוק את התיקייה מכיוון שסטודנטים אחרים פתחו בתוכה תתי-תיקיות."

        return True, ""

    return False, "סוג אובייקט לא מוכר למערכת המחיקות."

# ==============================================
# 4. Extract text from PDFs for smart search
# ==============================================
def extract_text_from_pdf(file_field):
    """
    Open a PDF, extract clean text from it, and return the result as a string.
    Limited to 20 pages to keep performance predictable.
    """
    import PyPDF2  # Imported lazily so the whole site does not pay the cost unless needed
    text = ""
    try:
        # Open the file for reading
        pdf_reader = PyPDF2.PdfReader(file_field)
        
        # Check how many pages exist, capped at 20
        num_pages = min(len(pdf_reader.pages), 20)
        
        for page_num in range(num_pages):
            page = pdf_reader.pages[page_num]
            # Extract text from the page and append it
            extracted = page.extract_text()
            if extracted:
                text += extracted + " "
                
    except Exception as e:
        # Print the error to the server log for debugging
        print(f"Error extracting text from PDF: {e}")
    
    return text.strip()

# ==============================================
# 5. Extract text from Word files (`.docx`) for smart search
# ==============================================        

from docx import Document as DocxReader

def extract_text_from_docx(file_field):
    """Extract text from a Word (`.docx`) file."""
    try:
        # Open the file directly from Django's file field
        doc = DocxReader(file_field)
        full_text = []
        for para in doc.paragraphs:
            if para.text:
                full_text.append(para.text)
        return '\n'.join(full_text)
    except Exception as e:
        print(f"Error extracting word text: {e}")
        return ""

# ==============================================
# 6. Networking & Security helpers
# ==============================================

def get_client_ip(request):
    """
    מחלץ את כתובת ה-IP האמיתית של המשתמש.
    בודק קודם האם המשתמש מאחורי שרת מתווך (Proxy) כמו ב-Render או DigitalOcean.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # במידה ויש רשימת כתובות, הכתובת הראשונה היא ה-IP המקורית של המשתמש
        ip = x_forwarded_for.split(',')[0]
    else:
        # במידה ולא, לוקחים את הכתובת הישירה מהבקשה
        ip = request.META.get('REMOTE_ADDR')
    return ip