from types import SimpleNamespace
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory

from core.models import CoinTransaction, Course, Major, Notification, University
from core.tests.base import BaseTestCase
from core.utils import (
    InsufficientFunds,
    get_client_ip,
    process_transaction,
    send_notification,
    validate_file_size,
    validate_file_type,
)


class UtilsTests(BaseTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="coin_user", email="coin@example.com", password="StrongPass123!"
        )
        self.university = University.objects.create(name="Test University")
        self.major = Major.objects.create(name="Engineering", university=self.university)
        self.course = Course.objects.create(name="Statics", major=self.major)
        self.factory = RequestFactory()

    def test_validate_file_size_enforces_image_limit(self):
        oversized_image = SimpleNamespace(name="photo.jpg", size=5 * 1024 * 1024 + 1)
        with self.assertRaises(ValidationError):
            validate_file_size(oversized_image)

        ok_image = SimpleNamespace(name="photo.jpg", size=5 * 1024 * 1024)
        validate_file_size(ok_image)

    def test_validate_file_size_enforces_document_limit(self):
        oversized_doc = SimpleNamespace(name="doc.pdf", size=1 * 1024 * 1024 + 1)
        with self.assertRaises(ValidationError):
            validate_file_size(oversized_doc)

        ok_doc = SimpleNamespace(name="doc.pdf", size=1 * 1024 * 1024)
        validate_file_size(ok_doc)

    def test_validate_file_type_accepts_pdf_and_resets_cursor(self):
        pdf_file = SimpleUploadedFile(
            "notes.pdf",
            b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF",
            content_type="application/pdf",
        )
        validate_file_type(pdf_file)
        self.assertEqual(pdf_file.read(4), b"%PDF")

    @mock.patch("core.utils.filetype.guess", return_value=None)
    def test_validate_file_type_rejects_unknown(self, mocked_guess):
        unknown_file = SimpleUploadedFile("notes.bin", b"not-a-real-file")
        with self.assertRaises(ValidationError):
            validate_file_type(unknown_file)
        mocked_guess.assert_called_once()

    @mock.patch(
        "core.utils.filetype.guess",
        return_value=SimpleNamespace(mime="application/x-msdownload", extension="exe"),
    )
    def test_validate_file_type_rejects_disallowed_mime(self, mocked_guess):
        exe_file = SimpleUploadedFile("malware.exe", b"MZ1234")
        with self.assertRaises(ValidationError):
            validate_file_type(exe_file)
        mocked_guess.assert_called_once()

    def test_send_notification_sets_target_object(self):
        send_notification(
            recipient=self.user,
            notification_type="system",
            title="New alert",
            message="Check the course",
            target_object=self.course,
        )
        notification = Notification.objects.get(user=self.user)
        self.assertEqual(notification.content_object, self.course)

    def test_process_transaction_updates_balances_and_notifies(self):
        profile = self.user.profile
        profile.current_balance = 5
        profile.lifetime_coins = 10
        profile.save()

        tx = process_transaction(
            user=self.user,
            amount=5,
            tx_type="system",
            description="Bonus",
            notify=True,
        )
        profile.refresh_from_db()
        self.assertEqual(profile.current_balance, 10)
        self.assertEqual(profile.lifetime_coins, 15)
        self.assertEqual(CoinTransaction.objects.count(), 1)
        self.assertEqual(Notification.objects.filter(user=self.user).count(), 1)
        self.assertEqual(tx.balance_before, 5)
        self.assertEqual(tx.balance_after, 10)

    def test_process_transaction_rejects_insufficient_funds(self):
        profile = self.user.profile
        profile.current_balance = 0
        profile.save()

        with self.assertRaises(InsufficientFunds):
            process_transaction(user=self.user, amount=-1, tx_type="spend", notify=False)

        profile.refresh_from_db()
        self.assertEqual(profile.current_balance, 0)
        self.assertEqual(CoinTransaction.objects.count(), 0)

    def test_get_client_ip_prefers_forwarded_header(self):
        request = self.factory.get("/", HTTP_X_FORWARDED_FOR="1.2.3.4, 5.6.7.8")
        self.assertEqual(get_client_ip(request), "1.2.3.4")

        request = self.factory.get("/", REMOTE_ADDR="9.9.9.9")
        self.assertEqual(get_client_ip(request), "9.9.9.9")
