from unittest import mock

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

from core.models import Course, Document, Major, Notification, University, UserCourseSelection
from core.tests.base import BaseLiveServerTestCase


@override_settings(
    ACCOUNT_EMAIL_VERIFICATION="none",
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class LiveJourneyTests(BaseLiveServerTestCase):
    def setUp(self):
        self.password = "StrongPass123!"
        self.user = get_user_model().objects.create_user(
            username="journey_user", email="journey@example.com", password=self.password
        )
        self.user.first_name = "Journey"
        self.user.save()
        self.user.profile.phone_number = "0501234567"
        self.user.profile.save()
        self.university = University.objects.create(name="Journey University")
        self.major = Major.objects.create(name="Physics", university=self.university)
        self.course = Course.objects.create(name="Quantum Mechanics", major=self.major)
        site = Site.objects.get_current()
        social_app = SocialApp.objects.create(
            provider="google",
            name="Google",
            client_id="test-client",
            secret="test-secret",
        )
        social_app.sites.add(site)

    def test_user_journey_uploads_and_sees_drive(self):
        self.assertTrue(self.client.login(username="journey_user", password=self.password))

        response = self.client.get(reverse("course_detail", args=[self.course.id]))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse("toggle_favorite_course", args=[self.course.id]))
        self.assertTrue(response.json()["is_favorite"])
        self.assertTrue(UserCourseSelection.objects.filter(user=self.user, course=self.course, is_starred=True).exists())

        pdf_file = SimpleUploadedFile(
            "lecture.pdf",
            b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF",
            content_type="application/pdf",
        )
        response = self.client.post(
            reverse("course_detail", args=[self.course.id]),
            data={"action": "quick_upload", "folder_id": "root", "file": [pdf_file]},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.json()["count"], 1)
        self.assertTrue(Notification.objects.filter(user=self.user, notification_type="economy").exists())

        response = self.client.get(reverse("personal_drive"))
        self.assertEqual(response.status_code, 200)
        uploaded_files = list(response.context["uploaded_files"])
        self.assertEqual(len(uploaded_files), 1)
        self.assertEqual(uploaded_files[0].title, "lecture")

    @mock.patch("core.utils.extract_text_from_pdf", return_value="quantum entanglement lecture notes")
    def test_global_search_finds_documents_by_extracted_content(self, mocked_extract):
        self.client.login(username="journey_user", password=self.password)

        pdf_file = SimpleUploadedFile(
            "quantum.pdf",
            b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF",
            content_type="application/pdf",
        )
        document = Document.objects.create(
            course=self.course,
            title="Quantum Notes",
            file=pdf_file,
            uploaded_by=self.user,
        )

        response = self.client.get(reverse("global_search"), {"q": "entanglement"})

        self.assertEqual(response.status_code, 200)
        self.assertIn(document, response.context["documents"])

    @mock.patch("core.utils.extract_text_from_pdf", return_value="")
    def test_personal_drive_orders_uploads_by_course_name(self, mocked_extract):
        self.client.login(username="journey_user", password=self.password)

        other_major = Major.objects.create(name="Mathematics", university=self.university)
        other_course = Course.objects.create(name="Algebra", major=other_major)

        first_file = SimpleUploadedFile(
            "zeta.pdf",
            b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF",
            content_type="application/pdf",
        )
        second_file = SimpleUploadedFile(
            "alpha.pdf",
            b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF",
            content_type="application/pdf",
        )

        Document.objects.create(course=self.course, title="zeta-upload", file=first_file, uploaded_by=self.user)
        Document.objects.create(course=other_course, title="alpha-upload", file=second_file, uploaded_by=self.user)

        response = self.client.get(reverse("personal_drive"))

        self.assertEqual(response.status_code, 200)
        uploaded_files = list(response.context["uploaded_files"])
        self.assertEqual([doc.title for doc in uploaded_files], ["alpha-upload", "zeta-upload"])
