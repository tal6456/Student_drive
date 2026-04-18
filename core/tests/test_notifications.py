"""
Unit tests for the Notification system
=======================================

This file tests the notification creation, resolution, and API endpoints
to ensure the system works correctly after the upgrade.
"""

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from core.models import Notification, Document, Course, Comment, Post
from core.utils import send_notification


class NotificationSystemTestCase(TestCase):
    def setUp(self):
        """Set up test data."""
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.user.profile.phone_number = '123456789'
        self.user.profile.save()
        
        self.other_user = get_user_model().objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123',
            first_name='Other',
            last_name='User'
        )
        self.other_user.profile.phone_number = '987654321'
        self.other_user.profile.save()
        
        # Create test objects
        self.course = Course.objects.create(
            name='Test Course',
            course_number='12345'
        )
        self.document = Document.objects.create(
            title='Test Document',
            course=self.course,
            uploaded_by=self.user
        )
        self.post = Post.objects.create(
            user=self.other_user,
            content='Test post'
        )

    def test_send_notification_without_target_object(self):
        """Test creating a notification without a target object."""
        send_notification(
            recipient=self.user,
            notification_type='system',
            title='Test Notification',
            message='This is a test message'
        )
        
        notification = Notification.objects.get(user=self.user)
        self.assertEqual(notification.title, 'Test Notification')
        self.assertEqual(notification.message, 'This is a test message')
        self.assertEqual(notification.notification_type, 'system')
        self.assertFalse(notification.is_read)
        self.assertIsNone(notification.content_object)

    def test_send_notification_with_target_object(self):
        """Test creating a notification with a target object."""
        send_notification(
            recipient=self.user,
            notification_type='system',
            title='Document Notification',
            message='Check this document',
            target_object=self.document
        )
        
        notification = Notification.objects.get(user=self.user)
        self.assertEqual(notification.title, 'Document Notification')
        self.assertEqual(notification.content_object, self.document)
        self.assertFalse(notification.is_read)

    def test_resolve_notification_marks_as_read(self):
        """Test that resolving a notification marks it as read."""
        notification = Notification.objects.create(
            user=self.user,
            title='Test',
            message='Test message',
            notification_type='system'
        )
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('resolve_notification', kwargs={'pk': notification.pk}))
        
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    def test_resolve_notification_redirects_to_target_object(self):
        """Test that resolving redirects to the target object's URL."""
        send_notification(
            recipient=self.user,
            notification_type='system',
            title='Document Notification',
            message='Check this document',
            target_object=self.document
        )
        
        notification = Notification.objects.get(user=self.user)
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('resolve_notification', kwargs={'pk': notification.pk}))
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], self.document.get_absolute_url())

    def test_resolve_notification_redirects_to_profile_when_no_target(self):
        """Test that resolving redirects to profile when no target object."""
        notification = Notification.objects.create(
            user=self.user,
            title='Economy Notification',
            message='You earned coins',
            notification_type='economy'
        )
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('resolve_notification', kwargs={'pk': notification.pk}))
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('profile'))

    def test_unread_notifications_count_api(self):
        """Test the unread notifications count API endpoint."""
        # Create some notifications
        Notification.objects.create(user=self.user, title='Unread 1', message='Test', is_read=False)
        Notification.objects.create(user=self.user, title='Unread 2', message='Test', is_read=False)
        Notification.objects.create(user=self.user, title='Read', message='Test', is_read=True)
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('unread_notifications_count'))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['unread_count'], 2)

    def test_unread_notifications_count_requires_auth(self):
        """Test that the API requires authentication."""
        response = self.client.get(reverse('unread_notifications_count'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_get_absolute_url_methods(self):
        """Test that models have get_absolute_url methods."""
        self.assertTrue(hasattr(self.document, 'get_absolute_url'))
        self.assertTrue(hasattr(self.course, 'get_absolute_url'))
        self.assertTrue(hasattr(self.post, 'get_absolute_url'))
        
        # Test URLs contain expected patterns
        self.assertIn('/document/', self.document.get_absolute_url())
        self.assertIn('/course/', self.course.get_absolute_url())
        self.assertIn('/feed/', self.post.get_absolute_url())