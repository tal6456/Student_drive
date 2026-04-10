"""
סקריפט לייבוא נתונים.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'student_drive.settings')
django.setup()

from core.models import University, Major, Course

courses_data = [
    # שנה א'
    {"name": "חשבון דיפרנציאלי להנדסת חשמל", "number": "21219671", "year": 1},
    {"name": "אלגברה ליניארית להנדסת חשמל 1", "number": "21219511", "year": 1},
    {"name": "פיזיקה 1 - הנדסת חשמל", "number": "20311371", "year": 1},
    # שנה ב'
    {"name": "חדו\"א וקטורי להנדסת חשמל", "number": "21219631", "year": 2},
    {"name": "מבוא להנדסת חשמל", "number": "36111021", "year": 2},
    {"name": "מבוא למערכות ליניאריות", "number": "36112011", "year": 2},
    # שנה ג'
    {"name": "מבוא לעיבוד אותות", "number": "36113321", "year": 3},
    {"name": "מבוא לתהליכים אקראיים", "number": "36113061", "year": 3},
    {"name": "מעגלים אלקטרוניים ספרתיים", "number": "36113021", "year": 3},
]

def run_import():
    uni, _ = University.objects.get_or_create(name="אוניברסיטת בן-גוריון בנגב")
    major, _ = Major.objects.get_or_create(university=uni, name="הנדסת חשמל ומחשבים")

    for data in courses_data:
        course, created = Course.objects.update_or_create(
            course_number=data["number"],
            defaults={
                'name': data["name"],
                'year': data["year"],
                'major': major # הקורס מקושר למקצוע, שמקושר לאוניברסיטה
            }
        )
        print(f"עודכן/נוצר: {course.name}")

if __name__ == '__main__':
    run_import