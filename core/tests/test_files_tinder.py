from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from core.models import Course, Document, DocumentComment, Friendship, Major, University, Vote
from core.tests.base import BaseTestCase


class FilesTinderTests(BaseTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="tinder_user",
            email="tinder@example.com",
            password="StrongPass123!",
            first_name="Tinder",
        )
        self.friend = get_user_model().objects.create_user(
            username="tinder_friend",
            email="friend@example.com",
            password="StrongPass123!",
            first_name="Friend",
        )

        self.user.profile.phone_number = "0501234567"
        self.user.profile.save()
        self.friend.profile.phone_number = "0507654321"
        self.friend.profile.save()

        self.uni = University.objects.create(name="Match University")
        self.major = Major.objects.create(name="Computer Science", university=self.uni)
        self.favorite_course = Course.objects.create(name="Algorithms", major=self.major, year=2)
        self.other_course = Course.objects.create(name="History", major=self.major, year=2)

        self.user.profile.favorite_courses.add(self.favorite_course)

        Friendship.objects.create(user_from=self.user, user_to=self.friend, status="accepted")

        fav_file = SimpleUploadedFile("algorithms.pdf", b"%PDF-1.4\n%%EOF", content_type="application/pdf")
        other_file = SimpleUploadedFile("history.pdf", b"%PDF-1.4\n%%EOF", content_type="application/pdf")

        self.favorite_doc = Document.objects.create(
            course=self.favorite_course,
            title="Algorithms - Final Tips",
            file=fav_file,
            uploaded_by=self.friend,
        )
        self.other_doc = Document.objects.create(
            course=self.other_course,
            title="History - Chapter 1",
            file=other_file,
            uploaded_by=self.friend,
        )

    def test_files_tinder_requires_login(self):
        response = self.client.get(reverse("files_tinder"))
        self.assertEqual(response.status_code, 302)

    def test_files_tinder_prioritizes_favorite_course_document(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("files_tinder"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Algorithms - Final Tips")

    def test_files_tinder_orders_by_requested_tiers(self):
        self.client.force_login(self.user)

        # Favorite (tier 1)
        fav = self.favorite_doc

        # Same faculty non-favorite (tier 2)
        faculty_file = SimpleUploadedFile("faculty.pdf", b"%PDF-1.4\n%%EOF", content_type="application/pdf")
        faculty_doc = Document.objects.create(
            course=self.other_course,
            title="Faculty Tier File",
            file=faculty_file,
            uploaded_by=self.friend,
        )

        # Personal drive with no course match (tier 3)
        personal_file = SimpleUploadedFile("personal.pdf", b"%PDF-1.4\n%%EOF", content_type="application/pdf")
        personal_doc = Document.objects.create(
            course=None,
            title="Personal Tier File",
            file=personal_file,
            uploaded_by=self.user,
        )

        # First swipe should still keep tier order: favorite -> faculty -> personal.
        first = self.client.get(reverse("files_tinder"))
        self.assertContains(first, fav.title)

        self.client.post(
            reverse("files_tinder_swipe"),
            data={"document_id": fav.id, "action": "dislike"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        second = self.client.get(reverse("files_tinder"))
        self.assertContains(second, faculty_doc.title)

        self.client.post(
            reverse("files_tinder_swipe"),
            data={"document_id": faculty_doc.id, "action": "dislike"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        third = self.client.get(reverse("files_tinder"))
        self.assertContains(third, personal_doc.title)

    def test_files_tinder_popularity_wins_inside_same_tier(self):
        self.client.force_login(self.user)

        # Two favorite-course docs: higher social proof should come first.
        weak_file = SimpleUploadedFile("weak.pdf", b"%PDF-1.4\n%%EOF", content_type="application/pdf")
        strong_file = SimpleUploadedFile("strong.pdf", b"%PDF-1.4\n%%EOF", content_type="application/pdf")

        weak_doc = Document.objects.create(
            course=self.favorite_course,
            title="Favorite Weak",
            file=weak_file,
            uploaded_by=self.friend,
        )
        strong_doc = Document.objects.create(
            course=self.favorite_course,
            title="Favorite Strong",
            file=strong_file,
            uploaded_by=self.friend,
        )

        liker = get_user_model().objects.create_user(
            username="extra_liker",
            email="liker@example.com",
            password="StrongPass123!",
            first_name="Like",
        )
        liker.profile.phone_number = "0503333333"
        liker.profile.save()

        strong_doc.likes.add(self.user, self.friend, liker)
        DocumentComment.objects.create(document=strong_doc, user=self.user, text="great")
        DocumentComment.objects.create(document=strong_doc, user=self.friend, text="super")

        response = self.client.get(reverse("files_tinder"))
        self.assertContains(response, "Favorite Strong")

    def test_files_tinder_swipe_like_creates_vote_and_like(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("files_tinder_swipe"),
            data={"document_id": self.favorite_doc.id, "action": "like"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertTrue(Vote.objects.filter(user=self.user, document=self.favorite_doc, value=1).exists())
        self.assertTrue(self.favorite_doc.likes.filter(id=self.user.id).exists())

    def test_files_tinder_swipe_dislike_creates_negative_vote(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("files_tinder_swipe"),
            data={"document_id": self.favorite_doc.id, "action": "dislike"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertTrue(Vote.objects.filter(user=self.user, document=self.favorite_doc, value=-1).exists())
