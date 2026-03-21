import google.generativeai as genai
from django.conf import settings
import PyPDF2
from docx import Document  # הספריה שהתקנו קודם!
import io
import os

# הגדרת המפתח
genai.configure(api_key=settings.GEMINI_API_KEY)


class StudentAgent:
    def __init__(self, student_user):
        self.student = student_user
        # משתמשים ב-2.0 Flash - הדגם הכי מהיר ומדויק ל-2026
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.chat_session = None

    def _extract_text(self, file_obj):
        """מזהה סוג קובץ ומחלץ טקסט (PDF או Word)"""
        try:
            filename = file_obj.name.lower()
            # קוראים את התוכן פעם אחת לזיכרון
            content = file_obj.read()

            # חילוץ מ-PDF
            if filename.endswith('.pdf'):
                reader = PyPDF2.PdfReader(io.BytesIO(content))
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
                return text

            # חילוץ מ-Word (docx)
            elif filename.endswith('.docx'):
                doc = Document(io.BytesIO(content))
                return "\n".join([para.text for para in doc.paragraphs])

            # חילוץ מטקסט פשוט
            elif filename.endswith('.txt'):
                return content.decode('utf-8')

            return "סוג קובץ לא נתמך."

        except Exception as e:
            return f"שגיאה בקריאת הקובץ: {str(e)}"

    def generate_summary(self, file_obj):
        """מסכם קובץ Word או PDF"""
        content = self._extract_text(file_obj)
        if "שגיאה" in content or not content.strip():
            return content

        prompt = f"""
        אתה עוזר אקדמי אישי של סטודנט בשם {self.student.username}.
        סכם את חומר הלימוד הבא בצורה ברורה, ממוקדת ומאורגנת.
        הדגש מושגים מרכזיים ונוסחאות אם ישנן.
        כתוב בעברית רהוטה ונקייה (בלי כוכביות מיותרות).

        החומר:
        {content[:15000]} # מגבלה קטנה כדי לא להעמיס על ה-Prompt
        """

        response = self.model.generate_content(prompt)
        return response.text

    def create_quiz(self, file_obj, num_questions=3):
        """מייצר חידון על בסיס קובץ Word או PDF"""
        content = self._extract_text(file_obj)
        prompt = f"צור חידון של {num_questions} שאלות אמריקאיות על החומר הבא עם תשובות בסוף:\n\n{content[:10000]}"

        response = self.model.generate_content(prompt)
        return response.text

    def chat_with_context(self, user_question, context_text=""):
        """צ'אט אינטליגנטי מבוסס הקשר"""
        full_prompt = f"בהתבסס על חומר הלימוד הבא:\n{context_text}\n\nשאלה: {user_question}"
        response = self.model.generate_content(full_prompt)
        return response.text