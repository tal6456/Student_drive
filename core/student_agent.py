import google.generativeai as genai
from django.conf import settings
import PyPDF2
import io

# הגדרת המפתח (כדאי שיהיה ב-settings.py או ב-env)
genai.configure(api_key=settings.GEMINI_API_KEY)


class StudentAgent:
    def __init__(self, student_user):
        self.student = student_user
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.chat_session = None

    def _extract_text(self, file_obj):
        """חילוץ טקסט מ-PDF בצורה בטוחה"""
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(file_obj.read()))
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def generate_summary(self, file_obj):
        """פונקציה שמקבלת קובץ ומחזירה סיכום"""
        content = self._extract_text(file_obj)
        prompt = f"סכם את חומר הלימוד הבא בצורה ברורה לסטודנט, הדגש מושגים מרכזיים:\n\n{content}"

        response = self.model.generate_content(prompt)
        return response.text

    def create_quiz(self, file_obj, num_questions=3):
        """מייצר חידון אמריקאי על בסיס הקובץ"""
        content = self._extract_text(file_obj)
        prompt = f"צור חידון של {num_questions} שאלות אמריקאיות על החומר הבא עם תשובות בסוף:\n\n{content}"

        response = self.model.generate_content(prompt)
        return response.text

    def chat_with_context(self, user_question, context_text=""):
        """מענה לשאלות צ'אט בהתבסס על הקשר ספציפי"""
        full_prompt = f"בהתבסס על החומר הבא: {context_text}\n ענה על השאלה: {user_question}"
        response = self.model.generate_content(full_prompt)
        return response.text