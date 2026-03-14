from django.core.management.base import BaseCommand
from core.models import University, Major, Course, Folder


class Command(BaseCommand):
    help = 'טוען נתוני בסיס של הנדסת חשמל ומחשבים באוניברסיטת בן-גוריון'

    def handle(self, *args, **kwargs):
        self.stdout.write("מתחיל בטעינת נתונים... 🚀")

        # 1. יצירת האוניברסיטה
        bgu, created = University.objects.get_or_create(
            name="אוניברסיטת בן-גוריון בנגב",
            defaults={'domain': 'bgu.ac.il'}
        )
        if created:
            self.stdout.write(self.style.SUCCESS('נוצרה אוניברסיטה: בן-גוריון'))

        # 2. יצירת התואר
        ee_major, created = Major.objects.get_or_create(
            name="הנדסת חשמל ומחשבים",
            university=bgu
        )
        if created:
            self.stdout.write(self.style.SUCCESS('נוצר מסלול: הנדסת חשמל ומחשבים'))

        # 3. רשימת הקורסים (נשאב ישירות מהסילבוס)
        # year: 1=א, 2=ב, 3=ג, 4=ד | semester: 'א', 'ב', 'שנתי'
        courses_data = [
            # שנה א' - סמסטר א'
            {'name': 'חשבון דיפרנציאלי להנדסת חשמל', 'number': '21219671', 'year': 1, 'semester': 'א'},
            {'name': 'מבוא מתמטי למהנדסים', 'number': '36111081', 'year': 1, 'semester': 'א'},
            {'name': 'פיזיקה 1 - הנדסת חשמל', 'number': '20311371', 'year': 1, 'semester': 'א'},
            {'name': 'אלגברה ליניארית להנדסת חשמל 1', 'number': '21219511', 'year': 1, 'semester': 'א'},
            {'name': 'מתמטיקה דיסקרטית', 'number': '21216201', 'year': 1, 'semester': 'א'},

            # שנה א' - סמסטר ב'
            {'name': 'מערכות ספרתיות להנדסת חשמל ומחשבים', 'number': '36113231', 'year': 1, 'semester': 'ב'},
            {'name': 'חשבון אינטגרלי ומשוואות דיפרנציאליות', 'number': '21219681', 'year': 1, 'semester': 'ב'},
            {'name': 'אלגברה ליניארית להנדסת חשמל 2', 'number': '21219521', 'year': 1, 'semester': 'ב'},
            {'name': 'פיזיקה א2', 'number': '20311471', 'year': 1, 'semester': 'ב'},
            {'name': 'יסודות מדעי המחשב', 'number': '37111601', 'year': 1, 'semester': 'ב'},

            # שנה ב' - סמסטר א' (ג')
            {'name': 'חדו"א וקטורי להנדסת חשמל', 'number': '21219631', 'year': 2, 'semester': 'א'},
            {'name': 'אנליזת פוריה להנדסת חשמל', 'number': '21219901', 'year': 2, 'semester': 'א'},
            {'name': 'מבוא למחשבים', 'number': '36113201', 'year': 2, 'semester': 'א'},
            {'name': 'פיסיקה א3', 'number': '20312391', 'year': 2, 'semester': 'א'},
            {'name': 'מבוא להנדסת חשמל', 'number': '36111021', 'year': 2, 'semester': 'א'},

            # שנה ב' - סמסטר ב' (ד')
            {'name': 'מבוא למערכות ליניאריות', 'number': '36112011', 'year': 2, 'semester': 'ב'},
            {'name': 'מבוא להתקני מוליכים למחצה', 'number': '36112171', 'year': 2, 'semester': 'ב'},
            {'name': 'תורת הפונקציות המרוכבות', 'number': '21210071', 'year': 2, 'semester': 'ב'},
            {'name': 'מבוא לשיטות חישוביות', 'number': '36112251', 'year': 2, 'semester': 'ב'},
            {'name': 'שדות אלקטרומגנטיים', 'number': '36113011', 'year': 2, 'semester': 'ב'},
            {'name': 'תורת ההסתברות', 'number': '21219831', 'year': 2, 'semester': 'ב'},

            # שנה ג' - קורסי ליבה וחובה
            {'name': 'מבוא לעיבוד אותות', 'number': '36113321', 'year': 3, 'semester': 'א'},
            {'name': 'מבוא לתהליכים אקראיים', 'number': '36113061', 'year': 3, 'semester': 'א'},
            {'name': 'מבוא למעגלים אלקטרונים אנלוגיים', 'number': '36113661', 'year': 3, 'semester': 'א'},
            {'name': 'מעגלים אלקטרוניים ספרתיים', 'number': '36113021', 'year': 3, 'semester': 'ב'},
            {'name': 'מבוא להמרת אנרגיה', 'number': '36113031', 'year': 3, 'semester': 'א'},
            {'name': 'מבוא לבקרה', 'number': '36113581', 'year': 3, 'semester': 'א'},
            {'name': 'מבוא לתקשורת מודרנית', 'number': '36113221', 'year': 3, 'semester': 'א'},
            {'name': 'מבני נתונים', 'number': '37110341', 'year': 3, 'semester': 'ב'},
        ]

        # 4. תיקיות ברירת מחדל שניצור לכל קורס
        default_folders = ['סיכומי הרצאות', 'תרגולי בית (עבודות)', 'מבחנים ופתרונות', 'חומרי עזר נוספים']

        courses_created = 0
        folders_created = 0

        for c_data in courses_data:
            course, created = Course.objects.get_or_create(
                major=ee_major,
                name=c_data['name'],
                defaults={
                    'course_number': c_data['number'],
                    'year': c_data['year'],
                    'semester': c_data['semester']
                }
            )

            if created:
                courses_created += 1
                # יצירת התיקיות לקורס החדש
                for f_name in default_folders:
                    Folder.objects.create(name=f_name, course=course)
                    folders_created += 1

        self.stdout.write(self.style.SUCCESS(f'הטעינה הושלמה! 🎉'))
        self.stdout.write(self.style.SUCCESS(f'נוצרו {courses_created} קורסים חדשים ו-{folders_created} תיקיות.'))
