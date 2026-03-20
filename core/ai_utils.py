from django.conf import settings
from google import genai
import PyPDF2
import os


client = genai.Client(api_key=settings.GEMINI_API_KEY)

def extract_text_from_pdf(file_path):
    """פונקציה שפותחת את ה-PDF ומוציאה ממנו טקסט"""
    text = ""
    try:
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            num_pages = min(5, len(reader.pages))
            for i in range(num_pages):
                page_text = reader.pages[i].extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text


def generate_smart_summary(file_path):
    """שולח את הטקסט ל-Gemini ומחזיר סיכום בעברית"""

    # השורה הזו חייבת להיות פה כדי שהשרת ימשוך את המפתח בזמן אמת
    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    if not os.path.exists(file_path):
        return "שגיאה: הקובץ לא נמצא על השרת."

    text = extract_text_from_pdf(file_path)

    if not text.strip():
        return "לא הצלחנו לקרוא טקסט מהקובץ. ייתכן והוא סרוק כתמונה."

    prompt = f"""
         תכין לי תקציר ממוקד, קצר וברור בעברית של עד 15 שורות.
        הוראות עיצוב חובה:
        1. השתמש בנקודות (Bullet points) כדי לסדר את המידע.
        2. אל תשתמש בסימני כוכביות (** או *) בשום צורה. כתוב טקסט נקי וקריא.
        3. עד 15 שורות 

        הטקסט לסיכום:
        {text}
        """

    try:
        # לא נוגע במודל! נשאר בול כמו בגיטהאב שלך:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text
    except Exception as e:
        print(f"AI Generation Error: {e}")
        return "אופס! ה-AI נתקל בבעיה ביצירת הסיכום. נסה שוב מאוחר יותר."