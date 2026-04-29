from django.core.management.base import BaseCommand
from core.models import ShopItem


class Command(BaseCommand):
    help = 'Seed the shop with gift card items'

    def handle(self, *args, **options):
        items_to_create = [
            {
                'name': 'כרטיס מתנה Office Depot',
                'category': 'gift cards',
                'description': 'קנה כל מה שאתה צריך לכתיבה, טכנולוגיה וציוד משרדי בחנות Office Depot.',
                'price_coins': 60,
                'badge_label': 'הנחה משקה',
                'redemption_code': 'OFFICEDEPO-100',
                'redemption_instructions': 'כנסו ל-officedepo.co.il, בחרו את המוצרים, והשתמשו בקוד בתשלום.',
                'stock_quantity': None,
                'is_featured': True,
                'sort_order': 1,
            },
            {
                'name': 'קורס דיגיטלי מקוון',
                'category': 'gift cards',
                'description': 'גשת מלאה לספרייה של קורסים מקצועיים בנושאים שונים - תכנות, עיצוב, עסקים ועוד.',
                'price_coins': 45,
                'badge_label': 'חדש',
                'redemption_code': 'COURSE-ONLINE-1',
                'redemption_instructions': 'קבל את קוד הגישה שלך וכנס ל-learningplatform.co.il עם הקוד.',
                'stock_quantity': None,
                'is_featured': True,
                'sort_order': 2,
            },
            {
                'name': 'כרטיס מתנה דיגיטלי אמזון',
                'category': 'gift cards',
                'description': 'קנה כמעט הכל מאמזון - ספרים, אלקטרוניקה, בתי הספר וציוד משרדי.',
                'price_coins': 55,
                'badge_label': 'פופולרי',
                'redemption_code': 'AMAZON-DIGITAL-1',
                'redemption_instructions': 'השתמש בקוד הגישה באמזון כדי להוסיף את הסכום לחשבונך.',
                'stock_quantity': 5,
                'is_featured': True,
                'sort_order': 3,
            },
            {
                'name': 'מנוי שנתי לאתר Skillshare',
                'category': 'gift cards',
                'description': 'גישה ללמידה יצירתית עם אלפי קורסים בפוטוגרפיה, ג\'רפיקה, סרטונים ועוד.',
                'price_coins': 50,
                'badge_label': '',
                'redemption_code': 'SKILLSHARE-ANNUAL',
                'redemption_instructions': 'עברו ל-skillshare.com, קבלו את קוד ההפעלה ורשמו משתמש חדש.',
                'stock_quantity': 10,
                'is_featured': False,
                'sort_order': 4,
            },
            {
                'name': 'Udemy - קורסים מקצועיים',
                'category': 'gift cards',
                'description': 'בחרו מקורסים אלפיים בתכנות, עיצוב, שיווק, עסקים, קריירה ותחומים נוספים.',
                'price_coins': 40,
                'badge_label': '',
                'redemption_code': 'UDEMY-COURSE',
                'redemption_instructions': 'שתפו את הקוד עם חבר או השתמשו בעצמכם כדי לקנות קורסים.',
                'stock_quantity': 15,
                'is_featured': False,
                'sort_order': 5,
            },
        ]

        created = 0
        updated = 0

        for item_data in items_to_create:
            item, is_new = ShopItem.objects.update_or_create(
                redemption_code=item_data['redemption_code'],
                defaults=item_data
            )
            if is_new:
                created += 1
                self.stdout.write(self.style.SUCCESS(f'✅ Created: {item.name}'))
            else:
                updated += 1
                self.stdout.write(self.style.WARNING(f'🔄 Updated: {item.name}'))

        self.stdout.write(
            self.style.SUCCESS(f'\n✨ Completed! Created {created} items, updated {updated} items.')
        )
