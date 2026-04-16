from django.conf import settings
from google import genai
import PyPDF2


def extract_text_from_pdf(file_field):
    """Open a PDF file, including one stored on S3, and extract its text."""
    text = ""
    try:
        with file_field.open('rb') as f:
            reader = PyPDF2.PdfReader(f)
            num_pages = min(5, len(reader.pages))
            for i in range(num_pages):
                page_text = reader.pages[i].extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text


def generate_smart_summary(document):
    """Send the text to Gemini and return a Hebrew summary."""

    api_key = getattr(settings, 'GEMINI_API_KEY', None)

    if not api_key:
        return "מערכת ה-AI כרגע בטיפול ותחזור בקרוב."

    client = genai.Client(api_key=api_key)

    # Pull the file from the `Document` object; this also works for S3-backed storage
    file_field = document.file

    if not file_field:
        return "שגיאה: לא נמצא קובץ."

    text = extract_text_from_pdf(file_field)

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
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text
    except Exception as e:
        print(f"AI Generation Error: {e}")
        return "אופס! ה-AI נתקל בבעיה ביצירת הסיכום. נסה שוב מאוחר יותר."
