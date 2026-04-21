import json
from types import SimpleNamespace
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

from core.models import Course, DownloadLog, Document, ExternalResource, Major, University, UserCourseSelection
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
        self.user.first_name = "Viewer"
        self.user.save()
        self.user.profile.phone_number = "0501234567"
        self.user.profile.save()
        self.university = University.objects.create(name="Test University")
        self.major = Major.objects.create(name="Engineering", university=self.university)
        self.course = Course.objects.create(name="Thermodynamics", major=self.major)
        site = Site.objects.get_current()
        social_app = SocialApp.objects.create(
            provider="google",
            name="Google",
            client_id="test-client",
            secret="test-secret",
        )
        social_app.sites.add(site)

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

    def test_course_creator_can_edit_course(self):
        self.course.creator = self.user
        self.course.save(update_fields=["creator"])
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("edit_course", args=[self.course.id]),
            data={
                "major": self.major.id,
                "name": "Thermodynamics Advanced",
                "course_number": "12345",
                "year": 1,
                "semester": "A",
                "track": "general",
                "description": "updated",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.course.refresh_from_db()
        self.assertEqual(self.course.name, "Thermodynamics Advanced")

    def test_non_creator_cannot_edit_course(self):
        owner = get_user_model().objects.create_user(
            username="owner",
            email="owner@example.com",
            password="StrongPass123!",
        )
        self.course.creator = owner
        self.course.save(update_fields=["creator"])
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("edit_course", args=[self.course.id]),
            data={
                "major": self.major.id,
                "name": "Illegal Edit",
                "course_number": "12345",
                "year": 1,
                "semester": "A",
                "track": "general",
                "description": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.course.refresh_from_db()
        self.assertNotEqual(self.course.name, "Illegal Edit")

    def test_creator_cannot_delete_non_empty_course(self):
        self.course.creator = self.user
        self.course.save(update_fields=["creator"])
        Folder.objects.create(course=self.course, name="הרצאות", created_by=self.user)
        self.client.force_login(self.user)

        response = self.client.post(reverse("delete_course", args=[self.course.id]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Course.objects.filter(id=self.course.id).exists())

    def test_creator_can_delete_empty_course(self):
        self.course.creator = self.user
        self.course.save(update_fields=["creator"])
        self.client.force_login(self.user)

        response = self.client.post(reverse("delete_course", args=[self.course.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Course.objects.filter(id=self.course.id).exists())

    def test_admin_can_delete_any_course(self):
        owner = get_user_model().objects.create_user(
            username="owner2",
            email="owner2@example.com",
            password="StrongPass123!",
        )
        self.course.creator = owner
        self.course.save(update_fields=["creator"])
        Folder.objects.create(course=self.course, name="תרגולים", created_by=owner)

        admin = get_user_model().objects.create_user(
            username="admin",
            email="admin@example.com",
            password="StrongPass123!",
            is_staff=True,
        )
        self.client.force_login(admin)
        response = self.client.post(reverse("delete_course", args=[self.course.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Course.objects.filter(id=self.course.id).exists())

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

    def test_live_search_returns_matching_course(self):
        response = self.client.get(reverse("live_search"), {"q": "Ther"})
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertGreaterEqual(len(payload["results"]), 1)
        first_result = payload["results"][0]
        self.assertEqual(first_result["id"], self.course.id)
        self.assertEqual(first_result["url"], reverse("course_detail", args=[self.course.id]))

    @mock.patch("core.utils.extract_text_from_pdf", return_value="")
    def test_delete_uploaded_file_via_ajax(self, mocked_extract):
        self.client.force_login(self.user)
        pdf_file = SimpleUploadedFile(
            "delete-me.pdf",
            b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF",
            content_type="application/pdf",
        )
        document = Document.objects.create(
            course=self.course,
            title="delete-me",
            file=pdf_file,
            uploaded_by=self.user,
        )

        response = self.client.post(
            reverse("delete_item_ajax"),
            data=json.dumps({"type": "document", "id": document.id}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertFalse(Document.objects.filter(id=document.id).exists())

    @mock.patch("core.utils.extract_text_from_pdf", return_value="")
    def test_remove_from_history_deletes_only_the_current_users_log(self, mocked_extract):
        self.client.force_login(self.user)
        pdf_file = SimpleUploadedFile(
            "history.pdf",
            b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF",
            content_type="application/pdf",
        )
        document = Document.objects.create(
            course=self.course,
            title="history",
            file=pdf_file,
            uploaded_by=self.user,
        )
        log = DownloadLog.objects.create(user=self.user, document=document)

        response = self.client.post(reverse("remove_from_history", args=[log.id]))

        self.assertEqual(response.status_code, 302)
        self.assertFalse(DownloadLog.objects.filter(id=log.id).exists())
