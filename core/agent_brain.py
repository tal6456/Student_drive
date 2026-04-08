import os
import io
import PyPDF2
from docx import Document
from django.conf import settings
from google import genai  # ה-SDK החדש שאתה משתמש בו


class StudentAgentBrain:
    def __init__(self):
        # משיכת המפתח בצורה בטוחה
        api_key = getattr(settings, 'GEMINI_API_KEY', None)

        # אתחול רק אם יש מפתח, אחרת נשמור כ-None ונטפל בזה בפונקציות
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = None
            print("WARNING: GEMINI_API_KEY is missing! Agent will not work.")

        self.model_name = 'gemini-2.5-flash'

    def extract_text_from_agent_file(self, agent_file_obj):
        """חילוץ טקסט מ-PDF ו-Word עם תמיכה מלאה באחסון ענן"""
        try:
            file_field = agent_file_obj.file
            file_extension = file_field.name.split('.')[-1].lower()
            text = ""

            # פתיחת הקובץ בצורה בטוחה (מתאים גם ל-S3/DigitalOcean וגם למקומי)
            with file_field.open('rb') as f:
                content = f.read()
                print(f"DEBUG: File size read: {len(content)} bytes")

                if file_extension == 'pdf':
                    reader = PyPDF2.PdfReader(io.BytesIO(content))
                    print(f"DEBUG: PDF Pages: {len(reader.pages)}")
                    for i, page in enumerate(reader.pages):
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                        else:
                            print(f"DEBUG: Page {i + 1} is empty/scanned")

                elif file_extension == 'docx':
                    doc = Document(io.BytesIO(content))
                    # חילוץ טקסט מכל הפסקאות
                    text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
                    print(f"DEBUG: Word extraction complete")

                elif file_extension == 'txt':
                    text = content.decode('utf-8')

            final_text = text.strip()
            print(f"DEBUG: Success! Extracted {len(final_text)} characters.")
            return final_text

        except Exception as e:
            print(f"DEBUG: Error in extraction: {str(e)}")
            return ""

    def get_summary(self, text_content):
        """מייצר סיכום נקי ללא תווים מיוחדים"""
        if not self.client:
            return "מערכת ה-AI כרגע לא מוגדרת. אנא פנה למנהל האתר."

        if not text_content or len(text_content) < 10:
            return "לא נמצא טקסט מספיק לסיכום. וודא שהקובץ אינו סרוק כתמונה."

        prompt = f"""
        אתה עוזר לימודי אישי. סכם את הטקסט הבא בנקודות (Bullet points), בעברית.
        אל תשתמש בכוכביות (** או *) בעיצוב הטקסט. כתוב טקסט נקי וקריא.
        עד 10 שורות סיכום.

        החומר:
        {text_content[:15000]}
        """

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text
        except Exception as e:
            print(f"DEBUG AI Error: {str(e)}")
            return "אופס! ה-AI נתקל בקושי לסכם את הקובץ כרגע."

    def answer_question(self, question, context_text):
        """מענה על שאלות הסטודנט על בסיס החומר שהועלה"""
        if not self.client:
            return "מערכת ה-AI כרגע לא מוגדרת. אנא פנה למנהל האתר."

        if not context_text:
            context_text = "אין חומר לימוד זמין כרגע. ענה מהידע הכללי שלך."

        prompt = f"""
        חומר לימוד:
        {context_text[:12000]}

        שאלה: {question}

        הנחיה: ענה בעברית בצורה ברורה. אם המידע נמצא בחומר הלימוד, התבסס עליו. 
        אם לא, ענה מהידע הכללי שלך כעוזר אקדמי.
        """
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"שגיאה במענה לשאלה: {str(e)}"