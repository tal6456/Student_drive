"""
מה המטרה של הקובץ הזה
----------------------
קובץ ה-API משמש כצינור להעברת נתונים מהירה בין הלקוח (Client) לשרת. 
הוא מאפשר לבצע פעולות "מאחורי הקלעים" ללא צורך ברענון הדף כולו.

הקובץ מטפל ב:
1. טעינה דינמית (Dynamic Loading): שליפת מסלולי לימוד (Majors) לפי האוניברסיטה שנבחרה.
2. נירמול נתונים (Normalization): מנגנון חכם למניעת כפילויות של מוסדות לימוד (למשל: "טכניון" ו-"הטכניון").
3. יצירת נתונים מהירה (AJAX Create): הוספת אוניברסיטאות ומסלולים ישירות מתוך טפסי הרישום.
4. מחיקה גמישה (Generic Delete): פונקציה מאוחדת למחיקת מסמכים, תיקיות, פוסטים ותגובות 
   תוך בדיקת הרשאות קפדנית (מניעת מחיקה של תוכן על ידי מי שאינו הבעלים).
"""


import json
import re
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse

from core.models import University, Major, Document, Folder, Post, Comment



def normalize_string_for_comparison(text):
    if not text:
        return ""
    text = text.strip().lower()
    text = re.sub(r'[-_]+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text


def load_majors(request):
    university_id = request.GET.get('university')
    if university_id:
        majors = Major.objects.filter(university_id=university_id).order_by('name')
        return JsonResponse(list(majors.values('id', 'name')), safe=False)
    return JsonResponse([])


@require_POST
def add_university_ajax(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)

    try:
        data = json.loads(request.body)
        new_name = data.get('name', '').strip()

        if not new_name:
            return JsonResponse({'success': False, 'error': 'שם המוסד לא יכול להיות ריק.'})

        normalized_new_name = normalize_string_for_comparison(new_name)

        for uni in University.objects.all():
            if normalize_string_for_comparison(uni.name) == normalized_new_name:
                return JsonResponse({
                    'success': False,
                    'error': f'מוסד זה כבר קיים במערכת בשם "{uni.name}". אנא בחר אותו מהרשימה.'
                })

        new_uni = University.objects.create(name=new_name)
        return JsonResponse({'success': True, 'id': new_uni.id, 'name': new_uni.name})

    except Exception as e:
        return JsonResponse({'success': False, 'error': 'אירעה שגיאה בשרת. נסה שוב.'})


@require_POST
def add_major_ajax(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)

    try:
        data = json.loads(request.body)
        new_name = data.get('name', '').strip()
        uni_id = data.get('university_id')

        if not new_name or not uni_id:
            return JsonResponse({'success': False, 'error': 'חסרים נתונים ליצירת המסלול.'})

        try:
            university = University.objects.get(id=uni_id)
        except University.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'המוסד שנבחר אינו תקין.'})

        normalized_new_name = normalize_string_for_comparison(new_name)

        for major in Major.objects.filter(university=university):
            if normalize_string_for_comparison(major.name) == normalized_new_name:
                return JsonResponse({
                    'success': False,
                    'error': f'המסלול כבר קיים במוסד זה בשם "{major.name}".'
                })

        new_major = Major.objects.create(name=new_name, university=university)
        return JsonResponse({'success': True, 'id': new_major.id, 'name': new_major.name})

    except Exception as e:
        return JsonResponse({'success': False, 'error': 'אירעה שגיאה בשרת. נסה שוב.'})


@login_required
@require_POST
def delete_item_ajax(request):
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            item_type = data.get('type')
            item_id = data.get('id')
        else:
            item_type = request.POST.get('type')
            item_id = request.POST.get('id')

        if not item_type or not item_id:
            return JsonResponse({'success': False, 'error': 'חסרים נתונים למחיקה.'})

        obj = None
        if item_type == 'document':
            obj = get_object_or_404(Document, id=item_id)
        elif item_type == 'folder':
            obj = get_object_or_404(Folder, id=item_id)
        elif item_type == 'post':
            obj = get_object_or_404(Post, id=item_id)
        elif item_type == 'comment':
            obj = get_object_or_404(Comment, id=item_id)
        else:
            return JsonResponse({'success': False, 'error': 'סוג פריט לא נתמך.'})

        from core.utils import check_deletion_permission
        is_allowed, error_msg = check_deletion_permission(request.user, obj, item_type)

        if is_allowed:
            obj.delete()
            return JsonResponse({'success': True, 'message': 'הפריט נמחק בהצלחה.'})
        else:
            return JsonResponse({'success': False, 'error': error_msg})

    except Exception as e:
        return JsonResponse({'success': False, 'error': f'אירעה שגיאה בשרת: {str(e)}'})


@login_required
def unread_notifications_count(request):
    """
    מחזיר את מספר ההתראות שלא נקראו.
    עבור אדמינים: בודק גם אם יש דיווח זכויות יוצרים פתוח שדורש Pop-up.
    """
    from core.models import Notification, Report

    # 1. ספירת התראות רגילה לכל משתמש
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    data = {'unread_count': count}

    # 2. בדיקה מיוחדת לאדמינים (צוות האתר)
    if request.user.is_staff:
        # מחפשים את הדיווח האחרון על זכויות יוצרים שטרם טופל
        urgent_report = Report.objects.filter(reason='copyright', is_resolved=False).order_by('-created_at').first()

        if urgent_report:
            data['has_urgent_alert'] = True
            data['urgent_message'] = f"התקבל דיווח על הפרת זכויות יוצרים בקובץ: {urgent_report.document.title}"
            data['alert_id'] = urgent_report.id
            data['alert_link'] = f"/admin/core/report/{urgent_report.id}/change/"

    return JsonResponse(data)