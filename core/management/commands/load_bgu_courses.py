from django.core.management.base import BaseCommand
from core.models import University, Major, Course


class Command(BaseCommand):
    help = 'טוען קורסים להנדסת חשמל ומחשבים באונ\' בן גוריון מתוך הסילבוס'

    def handle(self, *args, **kwargs):
        # 1. יצירת/שליפת האוניברסיטה והמסלול
        bgu, _ = University.objects.get_or_create(name="אוניברסיטת בן-גוריון בנגב")
        ee_major, _ = Major.objects.get_or_create(university=bgu, name="הנדסת חשמל ומחשבים")

        # 2. הנתונים שחולצו מהסילבוס (שנים א', ב', ג' ומסלולי התמחות)
        courses_data = [
            # --- שנה א', סמסטר א' ---
            {"name": "חשבון דיפרנציאלי להנדסת חשמל", "number": "21219671", "year": 1, "sem": "A", "track": "general"},
            {"name": "מבוא מתמטי למהנדסים", "number": "36111081", "year": 1, "sem": "A", "track": "general"},
            {"name": "פיזיקה 1 - הנדסת חשמל", "number": "20311371", "year": 1, "sem": "A", "track": "general"},
            {"name": "אלגברה ליניארית להנדסת חשמל 1", "number": "21219511", "year": 1, "sem": "A", "track": "general"},
            {"name": "מתמטיקה דיסקרטית", "number": "21216201", "year": 1, "sem": "A", "track": "general"},

            # --- שנה א', סמסטר ב' ---
            {"name": "מערכות ספרתיות להנדסת חשמל ומחשבים", "number": "36113231", "year": 1, "sem": "B",
             "track": "general"},
            {"name": "חשבון אינטגרלי ומשוואות דיפרנציאליות רגילות", "number": "21219681", "year": 1, "sem": "B",
             "track": "general"},
            {"name": "אלגברה ליניארית להנדסת חשמל 2", "number": "21219521", "year": 1, "sem": "B", "track": "general"},
            {"name": "פיזיקה א2", "number": "20311471", "year": 1, "sem": "B", "track": "general"},
            {"name": "יסודות מדעי המחשב", "number": "37111601", "year": 1, "sem": "B", "track": "general"},

            # --- שנה ב', סמסטר א' ---
            {"name": "חדו\"א וקטורי להנדסת חשמל", "number": "21219631", "year": 2, "sem": "A", "track": "general"},
            {"name": "אנליזת פוריה להנדסת חשמל", "number": "21219901", "year": 2, "sem": "A", "track": "general"},
            {"name": "מבוא למחשבים", "number": "36113201", "year": 2, "sem": "A", "track": "general"},
            {"name": "פיסיקה א3", "number": "20312391", "year": 2, "sem": "A", "track": "general"},
            {"name": "מבוא להנדסת חשמל", "number": "36111021", "year": 2, "sem": "A", "track": "general"},

            # --- שנה ב', סמסטר ב' ---
            {"name": "מבוא למערכות ליניאריות", "number": "36112011", "year": 2, "sem": "B", "track": "general"},
            {"name": "מבוא להתקני מוליכים למחצה", "number": "36112171", "year": 2, "sem": "B", "track": "general"},
            {"name": "יסודות תורת הפונקציות המרוכבות", "number": "21210071", "year": 2, "sem": "B", "track": "general"},
            {"name": "מבוא לשיטות חישוביות", "number": "36112251", "year": 2, "sem": "B", "track": "general"},
            {"name": "מעבדת מבוא בחשמל", "number": "36112063", "year": 2, "sem": "B", "track": "general"},
            {"name": "שדות אלקטרומגנטיים", "number": "36113011", "year": 2, "sem": "B", "track": "general"},
            {"name": "תורת ההסתברות להנדסת חשמל", "number": "21219831", "year": 2, "sem": "B", "track": "general"},

            # --- שנה ג', סמסטר א' ---
            {"name": "מבוא לעיבוד אותות", "number": "36113321", "year": 3, "sem": "A", "track": "general"},
            {"name": "מבוא לתהליכים אקראיים", "number": "36113061", "year": 3, "sem": "A", "track": "general"},
            {"name": "מבוא למעגלים אלקטרונים אנלוגיים", "number": "36113661", "year": 3, "sem": "A",
             "track": "general"},

            # --- שנה ג', סמסטר ב' ---
            {"name": "מעגלים אלקטרוניים ספרתיים", "number": "36113021", "year": 3, "sem": "B", "track": "general"},

            # --- קורסי ליבה והתמחות (שנים ג'-ד') ---
            {"name": "מבוא להמרת אנרגיה", "number": "36113031", "year": 3, "sem": "A", "track": "energy"},
            {"name": "מבוא לאלקטרומגנטיות וגלים", "number": "36113651", "year": 3, "sem": "A",
             "track": "electromagnetics"},
            {"name": "מבוא לבקרה", "number": "36113581", "year": 3, "sem": "A", "track": "control"},
            {"name": "מבוא לתקשורת מודרנית", "number": "36113221", "year": 3, "sem": "A", "track": "communication"},
            {"name": "עיבוד ספרתי של אותות", "number": "36114781", "year": 3, "sem": "B", "track": "signal_processing"},
            {"name": "פיזיקה של התקני מוליכים למחצה", "number": "36113681", "year": 3, "sem": "A", "track": "vlsi"},
            {"name": "מבני נתונים", "number": "37110341", "year": 3, "sem": "A", "track": "computers"},
            {"name": "מבוא לפוטואלקטרוניקה", "number": "36111071", "year": 3, "sem": "A", "track": "electro_optics"},
            {"name": "מבוא לרשתות מחשבים", "number": "37110291", "year": 3, "sem": "B", "track": "networks"},
        ]

        count = 0
        for c in courses_data:
            course, created = Course.objects.get_or_create(
                name=c["name"],
                major=ee_major,
                defaults={
                    'course_number': c["number"],
                    'year': c["year"],
                    'semester': c["sem"],
                    'track': c["track"]
                }
            )
            if created:
                count += 1

        self.stdout.write(self.style.SUCCESS(f'✅ בהצלחה! נטענו {count} קורסים חדשים לאוניברסיטת בן גוריון.'))