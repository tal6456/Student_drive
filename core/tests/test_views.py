from types import SimpleNamespace
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

from core.models import Course, ExternalResource, Major, University, UserCourseSelection
from core.tests.base import BaseTestCase


@override_settings(
    ACCOUNT_EMAIL_VERIFICATION="none",
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class ViewTests(BaseTestCase):
    def setUp(self):
        self.password = "StrongPass123!"
        self.user = get_user_model().objects.create_user(
            username="viewer", email="viewer@example.com", password=self.password
        )
        self.university = University.objects.create(name="Test University")
        self.major = Major.objects.create(name="Engineering", university=self.university)
        self.course = Course.objects.create(name="Thermodynamics", major=self.major)

    def test_personal_drive_requires_login(self):
        response = self.client.get(reverse("personal_drive"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("account_login"), response.url)

    def test_signup_flow_creates_user(self):
        response = self.client.post(
            reverse("account_signup"),
            data={
                "username": "newuser",
                "email": "newuser@example.com",
                "password1": "AnotherPass123!",
                "password2": "AnotherPass123!",
                "terms_accepted": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(get_user_model().objects.filter(username="newuser").exists())

    def test_login_flow_authenticates_user(self):
        response = self.client.post(
            reverse("account_login"),
            data={"login": "viewer", "password": self.password},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_password_change_ajax(self):
        self.client.login(username="viewer", password=self.password)
        response = self.client.post(
            reverse("change_password"),
            data={
                "old_password": self.password,
                "new_password1": "NewPass123!@",
                "new_password2": "NewPass123!@",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

    def test_toggle_favorite_course_ajax(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("toggle_favorite_course", args=[self.course.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["is_favorite"])
        selection = UserCourseSelection.objects.get(user=self.user, course=self.course)
        self.assertTrue(selection.is_starred)

    def test_add_external_resource_ajax(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("add_external_resource"),
            data={"title": "External Link", "link": "https://example.com"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertTrue(ExternalResource.objects.filter(id=payload["id"]).exists())

    def test_quick_upload_accepts_valid_files(self):
        self.client.force_login(self.user)
        pdf_file = SimpleUploadedFile(
            "notes.pdf",
            b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF",
            content_type="application/pdf",
        )
        response = self.client.post(
            reverse("course_detail", args=[self.course.id]),
            data={"action": "quick_upload", "folder_id": "root", "file": [pdf_file]},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)

    @mock.patch(
        "core.utils.filetype.guess",
        return_value=SimpleNamespace(mime="application/x-msdownload", extension="exe"),
    )
    def test_quick_upload_rejects_invalid_file_type(self, mocked_guess):
        self.client.force_login(self.user)
        bad_file = SimpleUploadedFile("malware.exe", b"MZ1234")
        response = self.client.post(
            reverse("course_detail", args=[self.course.id]),
            data={"action": "quick_upload", "folder_id": "root", "file": [bad_file]},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 0)
