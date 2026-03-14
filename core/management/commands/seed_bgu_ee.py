from django.core.management.base import BaseCommand
from core.models import University, Major, Course


class Command(BaseCommand):
    help = 'טוען נתוני בסיס של הנדסת חשמל ומחשבים באוניברסיטת בן-גוריון'

    def handle(self, *args, **kwargs):
        self.stdout.write("מתחיל בטעינת נתונים... 🚀")

        uni_name = "אוניברסיטת בן-גוריון בנגב"
        bgu, created = University.objects.get_or_create(
            name=uni_name,
            defaults={'domain': 'bgu.ac.il'}
        )

        major_name = "הנדסת חשמל ומחשבים"
        ee_major, created = Major.objects.get_or_create(
            name=major_name,
            university=bgu
        )

        courses_data = [
            {'name': 'חשבון דיפרנציאלי להנדסת חשמל', 'number': '21219671', 'year': '1', 'semester': '1'},
            {'name': 'מבוא מתמטי למהנדסים', 'number': '36111081', 'year': '1', 'semester': '1'},
            {'name': 'פיזיקה 1 - הנדסת חשמל', 'number': '20311371', 'year': '1', 'semester': '1'},
            {'name': 'אלגברה ליניארית להנדסת חשמל 1', 'number': '21219511', 'year': '1', 'semester': '1'},
            {'name': 'מתמטיקה דיסקרטית', 'number': '21216201', 'year': '1', 'semester': '1'},

            {'name': 'מערכות ספרתיות להנדסת חשמל ומחשבים', 'number': '36113231', 'year': '1', 'semester': '2'},
            {'name': 'חשבון אינטגרלי ומשוואות דיפרנציאליות', 'number': '21219681', 'year': '1', 'semester': '2'},
            {'name': 'אלגברה ליניארית להנדסת חשמל 2', 'number': '21219521', 'year': '1', 'semester': '2'},
            {'name': 'פיזיקה א2', 'number': '20311471', 'year': '1', 'semester': '2'},
            {'name': 'יסודות מדעי המחשב', 'number': '37111601', 'year': '1', 'semester': '2'},

            {'name': 'חדו"א וקטורי להנדסת חשמל', 'number': '21219631', 'year': '2', 'semester': '1'},
            {'name': 'אנליזת פוריה להנדסת חשמל', 'number': '21219901', 'year': '2', 'semester': '1'},
            {'name': 'מבוא למחשבים', 'number': '36113201', 'year': '2', 'semester': '1'},
            {'name': 'פיסיקה א3', 'number': '20312391', 'year': '2', 'semester': '1'},
            {'name': 'מבוא להנדסת חשמל', 'number': '36111021', 'year': '2', 'semester': '1'},

            {'name': 'מבוא למערכות ליניאריות', 'number': '36112011', 'year': '2', 'semester': '2'},
            {'name': 'מבוא להתקני מוליכים למחצה', 'number': '36112171', 'year': '2', 'semester': '2'},
            {'name': 'תורת הפונקציות המרוכבות', 'number': '21210071', 'year': '2', 'semester': '2'},
            {'name': 'מבוא לשיטות חישוביות', 'number': '36112251', 'year': '2', 'semester': '2'},
            {'name': 'שדות אלקטרומגנטיים', 'number': '36113011', 'year': '2', 'semester': '2'},
            {'name': 'תורת ההסתברות', 'number': '21219831', 'year': '2', 'semester': '2'},

            {'name': 'מבוא לעיבוד אותות', 'number': '36113321', 'year': '3', 'semester': '1'},
            {'name': 'מבוא לתהליכים אקראיים', 'number': '36113061', 'year': '3', 'semester': '1'},
            {'name': 'מבוא למעגלים אלקטרונים אנלוגיים', 'number': '36113661', 'year': '3', 'semester': '1'},
            {'name': 'מעגלים אלקטרוניים ספרתיים', 'number': '36113021', 'year': '3', 'semester': '2'},
            {'name': 'מבוא להמרת אנרגיה', 'number': '36113031', 'year': '3', 'semester': '1'},
            {'name': 'מבוא לבקרה', 'number': '36113581', 'year': '3', 'semester': '1'},
            {'name': 'מבוא לתקשורת מודרנית', 'number': '36113221', 'year': '3', 'semester': '1'},
            {'name': 'מבני נתונים', 'number': '37110341', 'year': '3', 'semester': '2'},
        ]

        courses_created = 0

        for c_data in courses_data:
            course, created = Course.objects.get_or_create(
                major=ee_major,
                name=c_data['name']
            )

            course.course_number = c_data['number']
            course.year = c_data['year']

            if c_data['semester'] == '1':
                course.semester = 'א'
            elif c_data['semester'] == '2':
                course.semester = 'ב'
            else:
                course.semester = c_data['semester']

            course.save()

            if created:
                courses_created += 1

        self.stdout.write(
            self.style.SUCCESS(f'הטעינה הושלמה! 🎉 נוצרו/עודכנו {len(courses_data)} קורסים. המערכת תדאג לתיקיות.'))