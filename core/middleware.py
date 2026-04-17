from django.shortcuts import redirect
from django.urls import reverse


class ProfileCompletionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. בודקים אם המשתמש מחובר
        if request.user.is_authenticated:
            profile = getattr(request.user, 'profile', None)

            # 2. מגדירים רשימת דפים "לבנים" (כדי לא ליצור לופ אינסופי)
            # המשתמש חייב להיות מסוגל להגיע לדף ההשלמה, להתנתק, או לראות קבצי Static
            allowed_paths = [
                reverse('complete_profile'),
                reverse('account_logout'),
                '/admin/',  # מאפשר לך כניסה לניהול
            ]

            # בודקים אם הנתיב הנוכחי הוא לא אחד מהמאושרים ולא קובץ מדיה/סטטיק
            is_allowed = any(request.path.startswith(path) for path in allowed_paths)
            is_static = request.path.startswith('/static/') or request.path.startswith('/media/')

            if not is_allowed and not is_static:
                # 3. הבדיקה הקריטית: האם חסר טלפון או שם?
                if not request.user.first_name or not profile or not profile.phone_number:
                    return redirect('complete_profile')

        response = self.get_response(request)
        return response