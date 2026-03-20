from google import genai

client = genai.Client(api_key="AIzaSyCsbKRg-pkH5VSNNeg8YoFfZeiZY8Qem24")

try:
    print("מנסה לסכם עם המודל העדכני: gemini-2.0-flash...")
    response = client.models.generate_content(
        model="gemini-2.0-flash",  # שינינו מ-1.5 ל-2.0
        contents="היי, תכתוב לי משפט אחד בעברית על סטודנטים שחורשים למבחן"
    )
    print("\n--- תשובת ה-AI ---")
    print(response.text)
    print("------------------")
except Exception as e:
    print(f"\nשגיאה: {e}")