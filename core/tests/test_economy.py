from datetime import date
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from core.models import CoinTransaction, Course, Major, University, UserProfile, Document
from core.tests.base import BaseTestCase
from core.utils import InsufficientFunds, process_transaction


class EconomyBalanceTests(BaseTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="summary_user",
            email="summary@example.com",
            password="StrongPass123!",
            first_name="Summary",
        )

        # --- הפתרון: חוסמים את הבונוס היומי כדי שלא יפריע למתמטיקה ---
        self.user.profile.last_daily_bonus = date(2026, 4, 25)
        # --------------------------------------------------------

        self.user.profile.phone_number = "0501234567"
        self.user.profile.current_balance = 20
        self.user.profile.lifetime_coins = 20
        self.user.profile.save(update_fields=["phone_number", "current_balance", "lifetime_coins", "last_daily_bonus"])

        university = University.objects.create(name="Summary University")
        major = Major.objects.create(name="Summary Major", university=university)
        course = Course.objects.create(name="Summary Course", major=major)
        doc_file = SimpleUploadedFile(
            "summary.pdf",
            b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF",
            content_type="application/pdf",
        )
        self.document = Document.objects.create(
            course=course,
            title="Summary Doc",
            file=doc_file,
            uploaded_by=self.user,
        )
        self.client.force_login(self.user)

    def test_current_balance_and_lifetime_update_for_add_and_spend(self):
        profile = self.user.profile
        profile.current_balance = 10
        profile.lifetime_coins = 20
        profile.save(update_fields=["current_balance", "lifetime_coins"])

        process_transaction(
            user=self.user,
            amount=7,
            tx_type="system",
            description="credit",
            notify=False,
        )
        process_transaction(
            user=self.user,
            amount=-4,
            tx_type="spend",
            description="debit",
            notify=False,
        )

        profile.refresh_from_db()
        self.assertEqual(profile.current_balance, 13)
        self.assertEqual(profile.lifetime_coins, 27)

    def test_balance_reaching_exactly_zero_is_supported(self):
        profile = self.user.profile
        profile.current_balance = 5
        profile.lifetime_coins = 100
        profile.save(update_fields=["current_balance", "lifetime_coins"])

        tx = process_transaction(
            user=self.user,
            amount=-5,
            tx_type="spend",
            description="exactly zero",
            notify=False,
        )

        profile.refresh_from_db()
        self.assertEqual(profile.current_balance, 0)
        self.assertEqual(profile.lifetime_coins, 100)
        self.assertEqual(tx.balance_after, 0)

    def test_lifetime_coins_never_decrease_when_spending(self):
        profile = self.user.profile
        profile.current_balance = 8
        profile.lifetime_coins = 42
        profile.save(update_fields=["current_balance", "lifetime_coins"])

        process_transaction(
            user=self.user,
            amount=-3,
            tx_type="spend",
            description="buy feature",
            notify=False,
        )

        profile.refresh_from_db()
        self.assertEqual(profile.current_balance, 5)
        self.assertEqual(profile.lifetime_coins, 42)

    def test_spend_with_insufficient_balance_raises(self):
        profile = self.user.profile
        profile.current_balance = 1
        profile.lifetime_coins = 9
        profile.save(update_fields=["current_balance", "lifetime_coins"])

        with self.assertRaises(InsufficientFunds):
            process_transaction(
                user=self.user,
                amount=-2,
                tx_type="spend",
                description="too expensive",
                notify=False,
            )


class CoinTransactionModelTests(BaseTestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="ledger_user",
            email="ledger@example.com",
            password="StrongPass123!",
            first_name="Ledger",
        )
        self.actor = user_model.objects.create_user(
            username="ledger_actor",
            email="actor@example.com",
            password="StrongPass123!",
            first_name="Actor",
        )

    def test_transaction_type_amount_and_balance_after_are_recorded(self):
        profile = self.user.profile
        profile.current_balance = 2
        profile.lifetime_coins = 2
        profile.save(update_fields=["current_balance", "lifetime_coins"])

        tx = process_transaction(
            user=self.user,
            amount=5,
            tx_type="quality_bonus",
            description="quality bonus",
            notify=False,
        )

        self.assertEqual(tx.transaction_type, "quality_bonus")
        self.assertEqual(tx.amount, 5)
        self.assertEqual(tx.balance_before, 2)
        self.assertEqual(tx.balance_after, 7)

    def test_actor_field_is_persisted_on_transaction(self):
        tx = process_transaction(
            user=self.user,
            amount=1,
            tx_type="system",
            description="actor check",
            actor=self.actor,
            notify=False,
        )

        self.assertTrue(
            hasattr(tx, "actor_id"),
            "CoinTransaction.actor is missing. Add an actor FK and persist it in process_transaction().",
        )
        self.assertEqual(tx.actor, self.actor)


class DailyBonusLogicTests(BaseTestCase):
    # מותאם לקוד שלך - בונוס של מטבע אחד
    DAILY_BONUS_AMOUNT = 1

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="daily_user",
            email="daily@example.com",
            password="StrongPass123!",
            first_name="Daily",
        )
        self.user.profile.phone_number = "0501234567"
        self.user.profile.save(update_fields=["phone_number"])
        self.client.force_login(self.user)

    def test_userprofile_has_last_daily_bonus_field(self):
        field_names = {field.name for field in UserProfile._meta.fields}
        self.assertIn(
            "last_daily_bonus",
            field_names,
            "UserProfile.last_daily_bonus field is missing.",
        )

    @mock.patch("django.utils.timezone.localdate", return_value=date(2026, 4, 25))
    def test_first_visit_of_day_grants_daily_bonus_and_updates_last_daily_bonus(self, _mock_today):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

        profile = self.user.profile
        profile.refresh_from_db()
        self.assertEqual(profile.current_balance, self.DAILY_BONUS_AMOUNT)
        self.assertEqual(profile.lifetime_coins, self.DAILY_BONUS_AMOUNT)
        self.assertEqual(getattr(profile, "last_daily_bonus", None), date(2026, 4, 25))

    @mock.patch("django.utils.timezone.localdate", return_value=date(2026, 4, 25))
    def test_user_cannot_receive_daily_bonus_twice_same_day(self, _mock_today):
        self.client.get(reverse("home"))
        self.client.get(reverse("home"))

        profile = self.user.profile
        profile.refresh_from_db()
        # וודא שהאיזון נשאר 1 ולא עלה ל-2
        self.assertEqual(profile.current_balance, self.DAILY_BONUS_AMOUNT)


class AiSummaryCostTests(BaseTestCase):
    # מותאם לקוד שלך - עלות של 2 מטבעות
    AI_SUMMARY_COST = 2

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="summary_user",
            email="summary@example.com",
            password="StrongPass123!",
            first_name="Summary",
        )
        self.user.profile.phone_number = "0501234567"
        self.user.profile.current_balance = 20
        self.user.profile.lifetime_coins = 20
        self.user.profile.save(update_fields=["phone_number", "current_balance", "lifetime_coins"])

        university = University.objects.create(name="Summary University")
        major = Major.objects.create(name="Summary Major", university=university)
        course = Course.objects.create(name="Summary Course", major=major)
        doc_file = SimpleUploadedFile(
            "summary.pdf",
            b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF",
            content_type="application/pdf",
        )
        self.document = Document.objects.create(
            course=course,
            title="Summary Doc",
            file=doc_file,
            uploaded_by=self.user,
        )
        self.client.force_login(self.user)

    @mock.patch("core.views.documents.generate_smart_summary", return_value="תקציר תקין")
    def test_ai_summary_deducts_required_coin_cost(self, _mock_summary):
        response = self.client.get(reverse("summarize_document_ai", args=[self.document.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json().get("success"))

        self.user.profile.refresh_from_db()
        # בדיקה ש-20 פחות 2 זה אכן 18
        self.assertEqual(self.user.profile.current_balance, 20 - self.AI_SUMMARY_COST)

    @mock.patch("core.views.documents.generate_smart_summary", return_value="תקציר תקין")
    def test_ai_summary_fails_with_insufficient_funds(self, _mock_summary):
        profile = self.user.profile
        profile.current_balance = 0
        profile.save(update_fields=["current_balance"])

        response = self.client.get(reverse("summarize_document_ai", args=[self.document.id]))
        payload = response.json()
        self.assertFalse(payload.get("success"))
        # חיפוש הודעה בעברית כפי שמופיעה בקוד שלך
        self.assertIn("אין לך מספיק", payload.get("error", ""))