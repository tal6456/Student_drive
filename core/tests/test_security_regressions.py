from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse

from core.models import Course, Friendship, Major, Post, University
from core.tests.base import BaseTestCase


@override_settings(
    ACCOUNT_EMAIL_VERIFICATION="none",
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class SecurityRegressionTests(BaseTestCase):
    def setUp(self):
        self.password = "StrongPass123!"
        self.sender = get_user_model().objects.create_user(
            username="sender",
            email="sender@example.com",
            password=self.password,
        )
        self.sender.first_name = "Sender"
        self.sender.save(update_fields=["first_name"])
        self.sender.profile.phone_number = "0501234567"
        self.sender.profile.save(update_fields=["phone_number"])

        self.receiver = get_user_model().objects.create_user(
            username="receiver",
            email="receiver@example.com",
            password=self.password,
        )
        self.receiver.first_name = "Receiver"
        self.receiver.save(update_fields=["first_name"])
        self.receiver.profile.phone_number = "0501234568"
        self.receiver.profile.save(update_fields=["phone_number"])

        self.university = University.objects.create(name="Security University")
        self.major = Major.objects.create(name="Security Major", university=self.university)
        self.course = Course.objects.create(name="AppSec 101", major=self.major)
        self.post = Post.objects.create(user=self.sender, content="Initial post")

    def test_send_friend_request_rejects_get(self):
        self.client.force_login(self.sender)

        response = self.client.get(reverse("send_friend_request", args=[self.receiver.username]))

        self.assertEqual(response.status_code, 405)
        self.assertFalse(
            Friendship.objects.filter(user_from=self.sender, user_to=self.receiver, status="pending").exists()
        )

    def test_send_friend_request_accepts_post(self):
        self.client.force_login(self.sender)

        response = self.client.post(reverse("send_friend_request", args=[self.receiver.username]))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Friendship.objects.filter(user_from=self.sender, user_to=self.receiver, status="pending").exists()
        )

    def test_xss_payload_is_escaped_and_frontend_uses_textcontent(self):
        self.client.force_login(self.sender)
        payload = "<img src=x onerror=alert(1)>"

        comment_response = self.client.post(
            reverse("add_comment", args=[self.post.id]),
            data={"text": payload},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(comment_response.status_code, 200)
        self.assertEqual(
            comment_response.json()["text"],
            "&lt;img src=x onerror=alert(1)&gt;",
        )

        feed_response = self.client.get(reverse("community_feed"))
        self.assertEqual(feed_response.status_code, 200)
        self.assertContains(feed_response, "textP.textContent = data.text;")

        course_response = self.client.get(reverse("course_detail", args=[self.course.id]))
        self.assertEqual(course_response.status_code, 200)
        self.assertContains(course_response, "textP.textContent = data.text;")

        drive_response = self.client.get(reverse("personal_drive"))
        self.assertEqual(drive_response.status_code, 200)
        self.assertContains(drive_response, "textP.textContent = data.text;")
