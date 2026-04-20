"""Regression-focused unit tests for model, view, auth, and button flows."""

from unittest.mock import patch

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from core.admin import CoinTransactionAdmin
from core.models import (
    CoinTransaction,
    Course,
    Document,
    ExternalResource,
    Major,
    Notification,
    University,
    UserCourseSelection,
)
from core.utils import validate_file_size, validate_file_type


User = get_user_model()


@override_settings(
    SECRET_KEY="test-secret-key",
    SECURE_SSL_REDIRECT=False,
    STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage",
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    },
)
class SiteRegressionSuiteTests(TestCase):
    """Verify core business rules and button-driven flows remain stable."""

    IMAGE_SIZE_LIMIT_BYTES = 5 * 1024 * 1024
    QUICK_UPLOAD_LIMIT_MB = 1
    QUICK_UPLOAD_FILE_SIZE_BYTES = 2 * 1024 * 1024
    USER_PHONE = "0500000001"
    UPLOADER_PHONE = "0500000002"
    WATCHER_PHONE = "0500000003"

    def _request_after_optional_301(self, method, url):
        """Follow a single optional 301 redirect before asserting auth behavior."""
        response = getattr(self.client, method)(url)
        if response.status_code == 301:
            response = getattr(self.client, method)(response["Location"])
        return response

    def setUp(self):
        """Create shared users and academic objects for integration-style tests."""
        self.user = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="StrongPass123!",
            first_name="User",
        )
        self.user.profile.phone_number = self.USER_PHONE
        self.user.profile.save()

        self.uploader = User.objects.create_user(
            username="uploader",
            email="uploader@example.com",
            password="StrongPass123!",
            first_name="Uploader",
        )
        self.uploader.profile.phone_number = self.UPLOADER_PHONE
        self.uploader.profile.save()

        self.watcher = User.objects.create_user(
            username="watcher",
            email="watcher@example.com",
            password="StrongPass123!",
            first_name="Watcher",
        )
        self.watcher.profile.phone_number = self.WATCHER_PHONE
        self.watcher.profile.save()

        self.university = University.objects.create(name="Test University")
        self.major = Major.objects.create(university=self.university, name="Computer Science")
        self.course = Course.objects.create(
            major=self.major,
            name="Algorithms",
            course_number="CS101",
            year=1,
            semester="A",
        )

    def test_profile_signal_creates_profile_for_new_user(self):
        """Ensure a profile is auto-created by the post-save user signal."""
        created_user = User.objects.create_user(
            username="newuser",
            email="newuser@example.com",
            password="StrongPass123!",
        )
        self.assertIsNotNone(created_user.profile)

    def test_rank_name_uses_lifetime_coins_thresholds(self):
        """Ensure rank_name returns the expected tier string from lifetime coins."""
        self.user.profile.lifetime_coins = 1000
        self.user.profile.save(update_fields=["lifetime_coins"])
        self.assertEqual(self.user.profile.rank_name, "💎 אלוף דרייב")

    def test_document_signal_notifies_only_starred_users_except_uploader(self):
        """Ensure document upload signal creates notifications only for valid watchers."""
        UserCourseSelection.objects.create(user=self.watcher, course=self.course, is_starred=True)
        UserCourseSelection.objects.create(user=self.uploader, course=self.course, is_starred=True)

        file_obj = SimpleUploadedFile("notes.txt", b"signal payload", content_type="text/plain")
        Document.objects.create(
            course=self.course,
            title="Signal Test",
            file=file_obj,
            uploaded_by=self.uploader,
        )

        self.assertTrue(Notification.objects.filter(user=self.watcher).exists())
        self.assertFalse(Notification.objects.filter(user=self.uploader).exists())

    def test_colored_amount_returns_green_for_positive_coin_transaction(self):
        """Ensure admin display uses green styling for positive amounts."""
        tx = CoinTransaction.objects.create(user=self.user, amount=5, transaction_type="system")
        admin_view = CoinTransactionAdmin(CoinTransaction, AdminSite())
        html = str(admin_view.colored_amount(tx))
        self.assertIn("color: green", html)
        self.assertIn(">5<", html)

    def test_colored_amount_returns_red_for_negative_coin_transaction(self):
        """Ensure admin display uses red styling for negative amounts."""
        tx = CoinTransaction.objects.create(user=self.user, amount=-3, transaction_type="spend")
        admin_view = CoinTransactionAdmin(CoinTransaction, AdminSite())
        html = str(admin_view.colored_amount(tx))
        self.assertIn("color: red", html)
        self.assertIn(">-3<", html)

    def test_validate_file_size_rejects_image_larger_than_5mb(self):
        """Ensure image uploads above 5MB are blocked by file-size validation."""
        oversized_image = SimpleUploadedFile(
            "oversized.jpg",
            b"a" * (self.IMAGE_SIZE_LIMIT_BYTES + 1),
            content_type="image/jpeg",
        )
        with self.assertRaises(ValidationError):
            validate_file_size(oversized_image)

    def test_validate_file_type_rejects_unknown_file_signature(self):
        """Ensure file-type validation rejects spoofed files with unknown signatures."""
        spoofed_pdf = SimpleUploadedFile(
            "fake.pdf",
            b"this-is-not-a-real-pdf" * 200,
            content_type="application/pdf",
        )
        with self.assertRaises(ValidationError):
            validate_file_type(spoofed_pdf)

    def test_home_with_browse_query_renders_home_template(self):
        """Ensure browse-mode home request renders the expected template."""
        response = self.client.get(reverse("home"), {"browse": "1"}, follow=True)
        self.assertEqual(response.status_code, 200)
        if response.redirect_chain:
            self.assertEqual(response.redirect_chain[0][1], 301)
        self.assertTemplateUsed(response, "core/home.html")

    def test_personal_drive_requires_login(self):
        """Ensure personal drive page is protected for unauthenticated visitors."""
        response = self._request_after_optional_301("get", reverse("personal_drive"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])

    def test_add_external_resource_button_creates_resource_with_ajax(self):
        """Ensure the add-external button endpoint creates a resource via AJAX POST."""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("add_external_resource"),
            {"title": "Django Docs", "link": "https://docs.djangoproject.com"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ExternalResource.objects.filter(user=self.user).count(), 1)
        self.assertTrue(response.json()["success"])

    def test_toggle_favorite_button_requires_login(self):
        """Ensure favorite-toggle button endpoint is inaccessible without authentication."""
        response = self._request_after_optional_301(
            "post",
            reverse("toggle_favorite_course", args=[self.course.id]),
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])

    def test_toggle_favorite_button_sets_starred_selection(self):
        """Ensure favorite-toggle button creates a starred user-course selection."""
        self.client.force_login(self.user)
        response = self.client.post(reverse("toggle_favorite_course", args=[self.course.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["is_favorite"])
        self.assertTrue(
            UserCourseSelection.objects.get(user=self.user, course=self.course).is_starred
        )

    def test_quick_upload_button_skips_files_above_limit(self):
        """Ensure quick upload endpoint ignores files larger than configured max size."""
        self.client.force_login(self.user)
        oversized = SimpleUploadedFile(
            "huge.pdf",
            b"x" * self.QUICK_UPLOAD_FILE_SIZE_BYTES,
            content_type="application/pdf",
        )

        with patch("core.utils.GLOBAL_MAX_FILE_SIZE_MB", self.QUICK_UPLOAD_LIMIT_MB):
            response = self.client.post(
                reverse("course_detail", args=[self.course.id]),
                {"action": "quick_upload", "folder_id": "root", "file": oversized},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 0)
        self.assertFalse(Document.objects.filter(uploaded_by=self.user, title="huge").exists())
