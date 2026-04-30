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


@shared_task
def generate_document_audio_task(document_id):
    """
    Background task: Generate audio file from document text for read-aloud feature.
    Runs asynchronously without blocking the user who requested it.
    
    Supports: .txt, .pdf, .docx and simple text content
    """
    import traceback
    from .models import Document, DocumentAudio
    from .tts_utils import extract_text_from_file, generate_audio_from_text
    from django.core.files.base import ContentFile

    try:
        doc = Document.objects.get(id=document_id)
        if not doc.file:
            print(f"Celery: No file attached to document {document_id}")
            return

        ext = doc.file_extension.lower()
        print(f"Celery: Starting audio generation for doc {document_id}, ext: {ext}")
        
        # Ensure DocumentAudio record exists
        audio_obj, created = DocumentAudio.objects.get_or_create(document=doc)
        if created:
            print(f"Celery: Created new DocumentAudio record for doc {document_id}")
        
        try:
            # Extract text from document
            print(f"Celery: Extracting text from {ext} file...")
            text = extract_text_from_file(doc.file, ext)
            
            if not text:
                print(f"Celery: No text extracted from doc {document_id}")
                audio_obj.is_generated = False
                audio_obj.save()
                return
            
            print(f"Celery: Extracted {len(text)} characters. Generating audio...")
            # Generate audio
            audio_bytes = generate_audio_from_text(text, language='he')
            
            if audio_bytes:
                # Save audio file
                filename = f"audio_{doc.id}_{os.urandom(4).hex()}.mp3"
                print(f"Celery: Saving audio file as {filename}...")
                audio_obj.audio_file.save(filename, ContentFile(audio_bytes), save=False)
                audio_obj.text_used = text[:500]  # Store first 500 chars as reference
                audio_obj.is_generated = True
                audio_obj.save()
                
                print(f"✅ Celery: Audio generated successfully for doc {document_id}")
            else:
                print(f"❌ Celery: Audio generation returned None for doc {document_id}")
                audio_obj.is_generated = False
                audio_obj.save()
                
        except Exception as text_error:
            print(f"❌ Celery: Error during audio generation for doc {document_id}")
            traceback.print_exc()
            audio_obj.is_generated = False
            audio_obj.save()

    except ObjectDoesNotExist:
        print(f"❌ Celery: Document {document_id} not found. Might have been deleted.")
    except Exception as e:
        print(f"❌ Celery: Error generating audio for doc {document_id}: {e}")
        traceback.print_exc()