from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import AgentKnowledge, Course  # Ensure the `Course` import remains valid
import json

# Initialize the agent brain once at module level
from .agent_brain import StudentAgentBrain

agent_brain = StudentAgentBrain()
@login_required
@csrf_exempt
def upload_agent_file(request):
    """Receive a file from the floating agent, save it, and return an initial summary."""
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        # Use the submitted course name; if missing, fall back to the generic label
        course_name = request.POST.get('course_name', 'כללי')

        # 1. Save the file in the agent storage
        agent_entry = AgentKnowledge.objects.create(
            owner=request.user,
            file=uploaded_file,
            course_name=course_name
        )

        # 2. Extract the text using the brain helper
        extracted_text = agent_brain.extract_text_from_agent_file(agent_entry)

        # 3. Persist the extracted text on the model
        agent_entry.extracted_text = extracted_text
        agent_entry.save()

        # 4. Generate a quick initial summary
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
    """Handle course-aware quiz generation, with a general-knowledge fallback when needed."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_question = data.get('question', '')

            # --- Step 1: request the course list for quiz creation ---
            if user_question == "GET_COURSES_FOR_QUIZ":
                # A. Pull courses from files the agent already knows about
                agent_courses = list(
                    AgentKnowledge.objects.filter(owner=request.user).values_list('course_name', flat=True).distinct())

                # B. Pull the courses shown on the site ("my semester") from the `Course` model
                semester_courses = list(Course.objects.all().values_list('name', flat=True))

                # C. Merge the lists so every visible course can appear as a button
                all_courses = list(set(agent_courses + semester_courses))

                # Filter out empty values, `None`, and the generic label so only real course names remain
                all_courses = [c for c in all_courses if c and c != "None" and c != "כללי"]

                # If the list is empty, return at least a generic option
                if not all_courses:
                    all_courses = ["כללי"]

                return JsonResponse({
                    'type': 'course_selection',
                    'answer': 'באיזה נושא תרצה את המבחן? בחר אחד מהקורסים שלך מהסמסטר:',
                    'courses': all_courses
                })

            # --- Step 2: attempt to create a quiz for the selected course ---
            if "בוחן בקורס:" in user_question:
                selected_course = user_question.split("בוחן בקורס:")[-1].strip()

                # Look up study material for this course in the agent database
                relevant_knowledge = AgentKnowledge.objects.filter(
                    owner=request.user,
                    course_name__icontains=selected_course
                ).values_list('extracted_text', flat=True)

                full_context = "\n".join(filter(None, relevant_knowledge))

                # --- New logic: if no material exists in the DB, offer a general-knowledge quiz ---
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

            # --- Step 3: create a general-knowledge question ---
            if "ייצר שאלות כלליות ב:" in user_question:
                topic = user_question.split("ייצר שאלות כלליות ב:")[-1].strip()
                general_quiz_instruction = (
                    f"המשתמש רוצה להיבחן על '{topic}' אך לא העלה קבצים. "
                    f"השתמש בידע הפנימי שלך כמומחה אקדמי בתחום וצור שאלה אמריקאית אחת ברמה גבוהה על '{topic}'. "
                    "הצג שאלה ו-4 אפשרויות (א, ב, ג, ד). אל תגלה את התשובה."
                )
                answer = agent_brain.answer_question(general_quiz_instruction, "")
                return JsonResponse({'type': 'text', 'answer': answer})

                # --- Step 4: regular question flow (context-aware RAG) ---
                # 1. Try to pull the current course name from the request, if it exists
                current_course = data.get('current_course', None)

                # 2. Start the query with only this user's files
                knowledge_query = AgentKnowledge.objects.filter(owner=request.user)

                if current_course and current_course != 'כללי':
                    # Super-focused path: if the user is asking from a course page, pull only that course's material
                    knowledge_query = knowledge_query.filter(course_name__icontains=current_course)
                else:
                    # Safety net: if the question comes from home or a generic course, keep it to the latest three items
                    knowledge_query = knowledge_query.order_by('-id')[:3]

                # 3. Fetch the text and combine it
                relevant_knowledge = knowledge_query.values_list('extracted_text', flat=True)
                full_context = "\n".join(filter(None, relevant_knowledge))

                # 4. Send the filtered text to Gemini
                answer = agent_brain.answer_question(
                    user_question,
                    full_context or "אין לי כרגע חומר רלוונטי בנושא זה. העלה קובץ כדי שנתחיל!"
                )
                return JsonResponse({'type': 'text', 'answer': answer})

        except Exception as e:
            return JsonResponse({'answer': f'שגיאה בעיבוד הבקשה: {str(e)}'}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=400)
