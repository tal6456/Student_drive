import os
from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist

@shared_task
def process_document_task(document_id):
    """
    משימת רקע: חילוץ טקסט למנוע חיפוש/AI ודחיסת תמונות.
    רצה מאחורי הקלעים מבלי לעכב את הסטודנט שהעלה את הקובץ.
    """
    from .models import Document
    from .utils import extract_text_from_pdf, extract_text_from_docx, compress_to_webp

    try:
        # שולפים את המסמך מתוך מסד הנתונים
        doc = Document.objects.get(id=document_id)
        if not doc.file:
            return

        ext = doc.file_extension.lower()
        updated_fields = []

        # 1. חילוץ טקסט למסמכים (PDF / DOCX)
        if not doc.file_content:
            try:
                if ext == '.pdf':
                    doc.file_content = extract_text_from_pdf(doc.file)
                    updated_fields.append('file_content')
                elif ext == '.docx':
                    doc.file_content = extract_text_from_docx(doc.file)
                    updated_fields.append('file_content')
            except Exception as e:
                print(f"Celery: Text extraction failed for doc {document_id}: {e}")

        # 2. דחיסת תמונות (JPG / PNG)
        image_extensions = ['.jpg', '.jpeg', '.png']
        if ext in image_extensions and not doc.file.name.endswith('.webp'):
            try:
                compressed_image = compress_to_webp(doc.file)
                if compressed_image:
                    new_name = f"{os.path.splitext(os.path.basename(doc.file.name))[0]}.webp"
                    # שמירת הקובץ הדחוס חזרה למערכת הקבצים
                    doc.file.save(new_name, compressed_image, save=False)
                    doc.file_extension = '.webp'
                    doc.file_size_bytes = doc.file.size
                    updated_fields.extend(['file', 'file_extension', 'file_size_bytes'])
            except Exception as e:
                print(f"Celery: Image compression failed for doc {document_id}: {e}")

        # אם עשינו שינוי (חילצנו טקסט או דחסנו), נשמור רק את השדות הרלוונטיים
        # זה מונע התנגשויות (Race conditions) מול המשתמש
        if updated_fields:
            doc.save(update_fields=updated_fields)

    except ObjectDoesNotExist:
        print(f"Celery: Document {document_id} not found. Might have been deleted.")
    except Exception as e:
        print(f"Celery: Unexpected error processing doc {document_id}: {e}")