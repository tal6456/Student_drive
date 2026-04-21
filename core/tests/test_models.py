import io
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from core.models import (
    CoinTransaction,
    Course,
    Document,
    ExternalResource,
    Folder,
    Major,
    Notification,
    University,
    UserCourseSelection,
    UserProfile,
)
from core.tests.base import BaseTestCase


def create_image_file(name="test.png", size=(1, 1), color=(10, 20, 30)):
    buffer = io.BytesIO()
    Image.new("RGB", size, color=color).save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


def create_pdf_file(name="notes.pdf"):
    return SimpleUploadedFile(
        name,
        b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF",
        content_type="application/pdf",
    )


class ModelTests(BaseTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="student", email="student@example.com", password="StrongPass123!"
        )
        self.university = University.objects.create(name="Test University")
        self.major = Major.objects.create(name="Computer Science", university=self.university)
        self.course = Course.objects.create(name="Algorithms", major=self.major)

    def test_profile_created_on_user_save(self):
        self.assertTrue(UserProfile.objects.filter(user=self.user).exists())
        self.user.first_name = "Updated"
        self.user.save()
        self.assertEqual(UserProfile.objects.filter(user=self.user).count(), 1)

    def test_rank_name_thresholds(self):
        profile = self.user.profile
        cases = [
            (0, "🥉 מתלמד"),
            (50, "🥈 תורם פעיל"),
            (200, "🥇 עורך נאמן"),
            (500, "🏆 אגדת סיכומים"),
            (1000, "💎 אלוף דרייב"),
        ]
        for coins, expected in cases:
            with self.subTest(coins=coins):
                profile.lifetime_coins = coins
                profile.save()
                self.assertEqual(profile.rank_name, expected)

    def test_university_logo_compresses_to_webp(self):
        logo = create_image_file("logo.png")
        university = University.objects.create(name="WebP Uni", logo=logo)
        self.assertTrue(university.logo.name.endswith(".webp"))

    def test_profile_picture_compresses_to_webp(self):
        profile = self.user.profile
        profile.profile_picture = create_image_file("profile.png")
        profile.save()
        self.assertTrue(profile.profile_picture.name.endswith(".webp"))

    def test_course_default_folder_tree_creates_hierarchy(self):
        self.course.create_default_folder_tree()
        root_folder = Folder.objects.get(course=self.course, name="הרצאות", parent__isnull=True)
        year_folder = Folder.objects.get(course=self.course, name="2020", parent=root_folder)
        semester_folder = Folder.objects.get(course=self.course, name="סמסטר א'", parent=year_folder)
        self.assertEqual(semester_folder.parent, year_folder)

    @mock.patch("core.utils.extract_text_from_pdf", return_value="extracted text")
    def test_document_save_sets_metadata_and_content(self, mocked_extract):
        doc = Document.objects.create(
            course=self.course,
            title="Lecture Notes",
            file=create_pdf_file(),
            uploaded_by=self.user,
        )
        self.assertEqual(doc.file_extension, ".pdf")
        self.assertGreater(doc.file_size_bytes, 0)
        self.assertEqual(doc.file_content, "extracted text")
        mocked_extract.assert_called_once()
        self.assertEqual(doc.get_absolute_url(), reverse("document_viewer", kwargs={"document_id": doc.id}))

    @mock.patch("core.utils.extract_text_from_pdf", return_value="")
    def test_new_document_notifies_starred_users(self, mocked_extract):
        subscriber = get_user_model().objects.create_user(
            username="subscriber", email="sub@example.com", password="StrongPass123!"
        )
        UserCourseSelection.objects.create(user=subscriber, course=self.course, is_starred=True)
        Document.objects.create(
            course=self.course,
            title="Shared Notes",
            file=create_pdf_file("shared.pdf"),
            uploaded_by=self.user,
        )
        notification = Notification.objects.get(user=subscriber, title__contains=self.course.name)
        self.assertTrue(Notification.objects.filter(user=subscriber, title__contains=self.course.name).exists())
        self.assertFalse(Notification.objects.filter(user=self.user, title__contains=self.course.name).exists())
        self.assertEqual(notification.link, reverse("course_detail", args=[self.course.id]))

    @mock.patch("core.utils.extract_text_from_pdf", return_value="")
    def test_new_document_notification_links_to_folder_page(self, mocked_extract):
        subscriber = get_user_model().objects.create_user(
            username="folder_subscriber", email="folder@example.com", password="StrongPass123!"
        )
        UserCourseSelection.objects.create(user=subscriber, course=self.course, is_starred=True)
        folder = Folder.objects.create(course=self.course, name="הרצאות", created_by=self.user)

        Document.objects.create(
            course=self.course,
            folder=folder,
            title="Folder Notes",
            file=create_pdf_file("folder.pdf"),
            uploaded_by=self.user,
        )

        notification = Notification.objects.get(user=subscriber, title__contains=self.course.name)
        expected_link = f"{reverse('course_detail_folder', args=[self.course.id, folder.id])}#folder_{folder.id}"
        self.assertEqual(notification.link, expected_link)

    @mock.patch("core.utils.extract_text_from_pdf", return_value="")
    def test_document_without_course_skips_notifications(self, mocked_extract):
        subscriber = get_user_model().objects.create_user(
            username="follower", email="follower@example.com", password="StrongPass123!"
        )
        UserCourseSelection.objects.create(user=subscriber, course=self.course, is_starred=True)
        Document.objects.create(
            course=None,
            title="Private Upload",
            file=create_pdf_file("private.pdf"),
            uploaded_by=self.user,
        )
        self.assertFalse(Notification.objects.filter(user=subscriber).exists())

    def test_external_resource_and_coin_transaction_str(self):
        resource = ExternalResource.objects.create(user=self.user, title="Cheat Sheet", link="https://example.com")
        tx = CoinTransaction.objects.create(user=self.user, amount=5, transaction_type="system")
        notification = Notification.objects.create(user=self.user, title="Notice", message="Hello")
        self.assertEqual(str(resource), "Cheat Sheet")
        self.assertIn("student", str(tx))
        self.assertIn("student", str(notification))
