from django.core.management.base import BaseCommand
from core.models import University, Major, Course


class Command(BaseCommand):
    help = 'טוען ומעדכן נתוני קורסים של בן-גוריון (חשמל ואזרחית-סביבתית)'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='מחק קורסים קיימים לפני הטעינה')

    def handle(self, *args, **kwargs):
        clear_data = kwargs['clear']
        self.stdout.write("🚀 מתחיל בתהליך ארגון הנתונים...")

        uni_name = "אוניברסיטת בן-גוריון בנגב"
        bgu, _ = University.objects.get_or_create(name=uni_name)

        # ניקוי המחלקה הכפולה (הנדסה אזרחית) אם היא קיימת
        Major.objects.filter(name="הנדסה אזרחית", university=bgu).delete()

        # --- 1. הנדסת חשמל ומחשבים ---
        ee_major, _ = Major.objects.get_or_create(name="הנדסת חשמל ומחשבים", university=bgu)
        if clear_data:
            Course.objects.filter(major=ee_major).delete()

        ee_courses = [
            {'name': 'חשבון דיפרנציאלי להנדסת חשמל', 'num': '21219671', 'y': 1, 's': 'A'},
            {'name': 'מבוא מתמטי למהנדסים', 'num': '36111081', 'y': 1, 's': 'A'},
            {'name': 'פיזיקה 1 - הנדסת חשמל', 'num': '20311371', 'y': 1, 's': 'A'},
            {'name': 'אלגברה ליניארית להנדסת חשמל 1', 'num': '21219511', 'y': 1, 's': 'A'},
            {'name': 'מתמטיקה דיסקרטית', 'num': '21216201', 'y': 1, 's': 'A'},
            {'name': 'מערכות ספרתיות להנדסת חשמל ומחשבים', 'num': '36113231', 'y': 1, 's': 'B'},
            {'name': 'חשבון אינטגרלי ומשוואות דיפרנציאליות', 'num': '21219681', 'y': 1, 's': 'B'},
            {'name': 'אלגברה ליניארית להנדסת חשמל 2', 'num': '21219521', 'y': 1, 's': 'B'},
            {'name': 'פיזיקה א2', 'num': '20311471', 'y': 1, 's': 'B'},
            {'name': 'יסודות מדעי המחשב', 'num': '37111601', 'y': 1, 's': 'B'},
        ]
        self.save_courses(ee_major, ee_courses)

        # --- 2. הנדסה אזרחית וסביבתית ---
        civil_env_major, _ = Major.objects.get_or_create(name="הנדסה אזרחית וסביבתית", university=bgu)
        if clear_data:
            Course.objects.filter(major=civil_env_major).delete()

        civil_env_courses = [
            # שנה א' [cite: 127, 130]
            {'name': 'אלגברה ליניארית להנדסה', 'num': '220119321', 'y': 1, 's': 'A'},
            {'name': 'חדו"א 1 להנדסה', 'num': '20119711', 'y': 1, 's': 'A'},
            {'name': 'גרפיקה הנדסית להנדסת בניין', 'num': '37411011', 'y': 1, 's': 'A'},
            {'name': 'מבוא למכניקת מבנים', 'num': '37411021', 'y': 1, 's': 'A'},
            {'name': 'מבוא לכימיה', 'num': '50051000', 'y': 1, 's': 'A'},
            {'name': 'חדו"א 2 להנדסה', 'num': '20119721', 'y': 1, 's': 'B'},
            {'name': 'פיסיקה ב1', 'num': '20311391', 'y': 1, 's': 'B'},
            {'name': 'חוזק 1 למהנדסי בניין', 'num': '37411051', 'y': 1, 's': 'B'},
            {'name': 'כימיה להנדסה אזרחית וסביבתית', 'num': '37411103', 'y': 1, 's': 'B'},
            {'name': 'מבוא לתכנות למהנדסים בפיתון', 'num': '37411681', 'y': 1, 's': 'B'},

            # שנה ב' [cite: 140, 143]
            {'name': 'משוואות דיפרנציאליות רגילות להנדסת בניין', 'num': '37412231', 'y': 2, 's': 'A'},
            {'name': 'כלכלה למהנדסי בניין', 'num': '37412311', 'y': 2, 's': 'A'},
            {'name': 'תכונות מכניות של חומרים', 'num': '37414117', 'y': 2, 's': 'A'},
            {'name': 'חוזק 2 למהנדסי בניין', 'num': '37412010', 'y': 2, 's': 'A'},
            {'name': 'סטטיקת מבנים 1', 'num': '37411081', 'y': 2, 's': 'A'},
            {'name': 'מבני בטון 1', 'num': '37412030', 'y': 2, 's': 'A'},
            {'name': 'מבוא להנדסה סביבתית', 'num': '37412032', 'y': 2, 's': 'A'},
            {'name': 'מבני בטון 2', 'num': '37412060', 'y': 2, 's': 'B'},
            {'name': 'גיאולוגיה למהנדסי בניין', 'num': '37412070', 'y': 2, 's': 'B'},
            {'name': 'חומרי בנייה', 'num': '37411061', 'y': 2, 's': 'B'},
            {'name': 'שיטות ביצוע בבנייה', 'num': '37412071', 'y': 2, 's': 'B'},
            {'name': 'סטטיקת מבנים 2', 'num': '37412020', 'y': 2, 's': 'B'},

            # שנה ג' [cite: 148, 159]
            {'name': 'פיזיקה ב2', 'num': '20311491', 'y': 3, 's': 'A'},
            {'name': 'מבוא לגיאומכניקה להנדסת בניין', 'num': '20617171', 'y': 3, 's': 'A'},
            {'name': 'סטטיסטיקה למהנדסי בניין', 'num': '37412101', 'y': 3, 's': 'A'},
            {'name': 'עיקרי תכן מבנים', 'num': '37413020', 'y': 3, 's': 'A'},
            {'name': 'מכניקת זורמים', 'num': '37413070', 'y': 3, 's': 'A'},
            {'name': 'מבני פלדה', 'num': '37412090', 'y': 3, 's': 'B'},
            {'name': 'אירועים חריגים 2: מבוא למיגון מבנים', 'num': '37414104', 'y': 3, 's': 'B'},
            {'name': 'הנדסת ביסוס', 'num': '37413041', 'y': 3, 's': 'B'},
            {'name': 'BIM ויישומים דיגיטליים בהנדסת מבנים', 'num': '37414035', 'y': 3, 's': 'B'},
        ]
        self.save_courses(civil_env_major, civil_env_courses)

        self.stdout.write(self.style.SUCCESS('🎉 הניקוי והעדכון הושלמו!'))

    def save_courses(self, major, data_list):
        for data in data_list:
            course, _ = Course.objects.update_or_create(
                major=major,
                name=data['name'],
                defaults={'course_number': data['num'], 'year': data['y'], 'semester': data['s'], 'track': 'general'}
            )
            course.create_default_folder_tree()
            self.stdout.write(f"  - [{major.name}] {course.name} מוכן.")