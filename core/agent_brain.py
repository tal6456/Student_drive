from django.conf import settings
from google import genai  # הספרייה החדשה
import PyPDF2
from docx import Document
import io


class StudentAgentBrain:
    def __init__(self):
        # שימוש ב-Client החדש ובמודל 2.5 כפי שמופיע בקוד שעובד לך
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = 'gemini-2.5-flash'

    def extract_text_from_agent_file(self, agent_file_obj):
        """חילוץ טקסט משופר עם הדפסות לדיבאג"""
        try:
            # גישה לקובץ
            file_field = agent_file_obj.file
            file_extension = file_field.name.split('.')[-1].lower()
            text = ""

            # פתיחת הקובץ לקריאה
            with file_field.open('rb') as f:
                content = f.read()
                print(f"DEBUG: File size read: {len(content)} bytes")  # הדפסה ללוג

                if file_extension == 'pdf':
                    reader = PyPDF2.PdfReader(io.BytesIO(content))
                    print(f"DEBUG: Number of pages in PDF: {len(reader.pages)}")

                    for i, page in enumerate(reader.pages):
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                        else:
                            print(f"DEBUG: Page {i + 1} is empty or scanned image")

                elif file_extension == 'docx':
                    doc = Document(io.BytesIO(content))
                    text = "\n".join([para.text for para in doc.paragraphs])

            # ניקוי רווחים מיותרים
            final_text = text.strip()
            print(f"DEBUG: Total characters extracted: {len(final_text)}")
            return final_text

        except Exception as e:
            print(f"DEBUG: Error extracting text: {str(e)}")
            return ""

    def get_summary(self, text_content):
        if not text_content:
            return "לא נמצא טקסט לסיכום."

        prompt = f"""
        אתה עוזר לימודי אישי. סכם את הטקסט הבא בנקודות, בעברית, ללא כוכביות:
        {text_content[:15000]}
        """

        try:
            # שינוי המבנה ל-syntax של ה-SDK החדש
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"שגיאה ב-AI: {str(e)}"

    def answer_question(self, question, context_text):
        prompt = f"""
        חומר לימוד: {context_text[:10000]}
        שאלה: {question}
        ענה בעברית על בסיס החומר בלבד.
        """
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"שגיאה במענה לשאלה: {str(e)}"