from django.contrib.auth import get_user_model
from django.urls import reverse

from core.models import CoinTransaction, ShopItem, ShopPurchase
from core.tests.base import BaseTestCase


class ShopFeatureTests(BaseTestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="shopper",
            email="shopper@example.com",
            password="StrongPass123!",
            first_name="Shopper",
            is_staff=True,
        )
        self.user.profile.phone_number = "0501234567"
        self.user.profile.current_balance = 100
        self.user.profile.lifetime_coins = 100
        self.user.profile.save(update_fields=["phone_number", "current_balance", "lifetime_coins"])
        self.client.force_login(self.user)

        self.featured_item = ShopItem.objects.create(
            name="Gift Card 100",
            category="gift cards",
            description="Digital reward card",
            price_coins=30,
            badge_label="חדש",
            redemption_code="GC-100-ABC",
            stock_quantity=2,
            is_featured=True,
            sort_order=1,
        )
        self.unlimited_item = ShopItem.objects.create(
            name="Online Course Code",
            category="gift cards",
            description="Access code for a course",
            price_coins=40,
            redemption_code="COURSE-XYZ",
            stock_quantity=None,
            sort_order=2,
        )

    def test_shop_page_loads_with_items(self):
        response = self.client.get(reverse("shop"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.featured_item.name)
        self.assertContains(response, self.unlimited_item.name)

    def test_staff_can_create_shop_item_from_shop_page(self):
        response = self.client.post(
            reverse("shop"),
            data={
                "name": "New Gift Card",
                "category": "gift cards",
                "description": "Created from the shop modal",
                "price_coins": 25,
                "badge_label": "חדש",
                "redemption_code": "NEW-GIFT-001",
                "redemption_instructions": "Send to the user after approval.",
                "stock_quantity": 10,
                "is_featured": "on",
                "is_active": "on",
                "sort_order": 5,
            },
        )

        self.assertEqual(response.status_code, 302)
        created_item = ShopItem.objects.get(redemption_code="NEW-GIFT-001")
        self.assertEqual(created_item.name, "New Gift Card")
        self.assertTrue(created_item.is_featured)

    def test_purchase_deducts_coins_and_creates_purchase_record(self):
        response = self.client.post(reverse("purchase_shop_item", args=[self.featured_item.id]))
        self.assertEqual(response.status_code, 302)

        self.user.profile.refresh_from_db()
        self.featured_item.refresh_from_db()

        self.assertEqual(self.user.profile.current_balance, 70)
        self.assertEqual(self.featured_item.stock_quantity, 1)
        self.assertEqual(ShopPurchase.objects.count(), 1)
        purchase = ShopPurchase.objects.get()
        self.assertEqual(purchase.item_name, self.featured_item.name)
        self.assertEqual(purchase.delivery_code, self.featured_item.redemption_code)
        self.assertEqual(CoinTransaction.objects.filter(transaction_type="purchase").count(), 1)

    def test_purchase_rejects_insufficient_funds(self):
        expensive_item = ShopItem.objects.create(
            name="Luxury Voucher",
            category="gift cards",
            description="Too expensive",
            price_coins=999,
            stock_quantity=None,
            sort_order=3,
        )

        response = self.client.post(reverse("purchase_shop_item", args=[expensive_item.id]))
        self.assertEqual(response.status_code, 302)

        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.current_balance, 100)
        self.assertEqual(ShopPurchase.objects.filter(item=expensive_item).count(), 0)

    def test_limited_stock_blocks_second_purchase(self):
        limited_item = ShopItem.objects.create(
            name="Limited Badge",
            category="accessories",
            description="Only one available",
            price_coins=10,
            stock_quantity=1,
            sort_order=4,
        )

        first = self.client.post(reverse("purchase_shop_item", args=[limited_item.id]))
        self.assertEqual(first.status_code, 302)

        second = self.client.post(reverse("purchase_shop_item", args=[limited_item.id]))
        self.assertEqual(second.status_code, 302)

        limited_item.refresh_from_db()
        self.assertEqual(limited_item.stock_quantity, 0)
        self.assertEqual(ShopPurchase.objects.filter(item=limited_item).count(), 1)

    def test_non_admin_user_cannot_purchase(self):
        non_admin_user = get_user_model().objects.create_user(
            username="regularuser",
            email="regular@example.com",
            password="StrongPass123!",
            first_name="Regular",
            is_staff=False,
        )
        self.client.force_login(non_admin_user)

        response = self.client.post(reverse("purchase_shop_item", args=[self.featured_item.id]))
        self.assertEqual(response.status_code, 302)

        self.assertEqual(ShopPurchase.objects.filter(user=non_admin_user).count(), 0)