from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import AgentKnowledge, Course  # וודא שהייבוא של Course תקין
import json

# אתחול המוח של הסוכן פעם אחת ברמת המודול
from .agent_brain import StudentAgentBrain

agent_brain = StudentAgentBrain()


@login_required
@csrf_exempt
def upload_agent_file(request):
    """
    View שמקבל קובץ מהסוכן הצף, שומר אותו ומחזיר סיכום ראשוני.
    """
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        # שימוש בשם הקורס שנשלח, אם לא קיים - ברירת מחדל 'כללי'
        course_name = request.POST.get('course_name', 'כללי')

        # 1. שמירת הקובץ במאגר של הסוכן
        agent_entry = AgentKnowledge.objects.create(
            owner=request.user,
            file=uploaded_file,
            course_name=course_name
        )

        # 2. חילוץ הטקסט (הפעלת הפונקציה מה-Brain)
        extracted_text = agent_brain.extract_text_from_agent_file(agent_entry)

        # 3. שמירת הטקסט המופק במודל
        agent_entry.extracted_text = extracted_text
        agent_entry.save()

        # 4. יצירת סיכום ראשוני מהיר
        summary = agent_brain.get_summary(extracted_text)

        return JsonResponse({
            'status': 'success',
            'message': 'הקובץ נלמד בהצלחה!',
            'summary': summary,
            'file_id': agent_entry.id
        })

    return JsonResponse({'status': 'error', 'message': 'לא התקבל קובץ תקין.'}, status=400)


@login_required
@csrf_exempt
def ask_agent_question(request):
    """
    View משופר המנהל זיהוי קורסים לסמסטר וייצור בוחן ממוקד עם מעבר לידע כללי במקרה הצורך.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_question = data.get('question', '')

            # --- שלב 1: בקשת רשימת קורסים לבוחן ---
            if user_question == "GET_COURSES_FOR_QUIZ":
                # א. שליפת קורסים מהקבצים שהסוכן כבר מכיר (הזיכרון של הסוכן)
                agent_courses = list(
                    AgentKnowledge.objects.filter(owner=request.user).values_list('course_name', flat=True).distinct())

                # ב. שליפת הקורסים שמופיעים באתר (הסמסטר שלי) מתוך מודל Course
                semester_courses = list(Course.objects.all().values_list('name', flat=True))

                # ג. איחוד הרשימות כדי שכל הקורסים שרואים בתמונה יופיעו ככפתורים
                all_courses = list(set(agent_courses + semester_courses))

                # סינון ערכים ריקים, None או "כללי" כדי להשאיר רק שמות קורסים אמיתיים
                all_courses = [c for c in all_courses if c and c != "None" and c != "כללי"]

                # אם הרשימה ריקה, נחזיר לפחות אופציה כללית או הודעה מתאימה
                if not all_courses:
                    all_courses = ["כללי"]

                return JsonResponse({
                    'type': 'course_selection',
                    'answer': 'באיזה נושא תרצה את המבחן? בחר אחד מהקורסים שלך מהסמסטר:',
                    'courses': all_courses
                })

            # --- שלב 2: ניסיון יצירת בוחן לקורס שנבחר ---
            if "בוחן בקורס:" in user_question:
                selected_course = user_question.split("בוחן בקורס:")[-1].strip()

                # חיפוש חומר לימוד ששייך לקורס הזה בבסיס הנתונים של הסוכן
                relevant_knowledge = AgentKnowledge.objects.filter(
                    owner=request.user,
                    course_name__icontains=selected_course
                ).values_list('extracted_text', flat=True)

                full_context = "\n".join(filter(None, relevant_knowledge))

                # --- לוגיקה חדשה: אם אין חומר ב-DB, נציע בוחן מידע כללי ---
                if not full_context:
                    return JsonResponse({
                        'type': 'general_knowledge_offer',
                        'course': selected_course,
                        'answer': f'עדיין לא העלית קבצים עבור "{selected_course}". תרצה שאצור לך שאלות מהידע הכללי שלי כבינה מלאכותית בנושא זה?'
                    })

                quiz_instruction = (
                    f"אתה Quiz Master מומחה לקורס '{selected_course}'. "
                    "בהתבסס על חומר הלימוד שסופק, צור שאלה אמריקאית אחת מאתגרת. "
                    "מבנה התשובה: הצג את השאלה ולאחריה 4 אפשרויות (א, ב, ג, ד). "
                    "אל תציין מהי התשובה הנכונה. המתן לתגובת הסטודנט."
                )

                answer = agent_brain.answer_question(quiz_instruction, full_context)
                return JsonResponse({'type': 'text', 'answer': answer})

            # --- שלב 3: יצירת שאלה מידע כללי (הפעלת מוח ה-AI) ---
            if "ייצר שאלות כלליות ב:" in user_question:
                topic = user_question.split("ייצר שאלות כלליות ב:")[-1].strip()
                general_quiz_instruction = (
                    f"המשתמש רוצה להיבחן על '{topic}' אך לא העלה קבצים. "
                    f"השתמש בידע הפנימי שלך כמומחה אקדמי בתחום וצור שאלה אמריקאית אחת ברמה גבוהה על '{topic}'. "
                    "הצג שאלה ו-4 אפשרויות (א, ב, ג, ד). אל תגלה את התשובה."
                )
                answer = agent_brain.answer_question(general_quiz_instruction, "")
                return JsonResponse({'type': 'text', 'answer': answer})

            # --- שלב 4: שאלה רגילה (RAG) ---
            all_knowledge = AgentKnowledge.objects.filter(owner=request.user).values_list('extracted_text', flat=True)
            full_context = "\n".join(filter(None, all_knowledge))

            answer = agent_brain.answer_question(user_question,
                                                 full_context or "אין חומר זמין כרגע. העלה קובץ כדי שנתחיל!")
            return JsonResponse({'type': 'text', 'answer': answer})

        except Exception as e:
            return JsonResponse({'answer': f'שגיאה בעיבוד הבקשה: {str(e)}'}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=400)