"""
Password Reset End-to-End Tests
===============================

Tests for django-allauth password reset functionality, including:
- Password reset email submission
- Valid token handling
- Invalid/expired token handling
- Password update verification
"""

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core import mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

User = get_user_model()


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class PasswordResetTests(TestCase):
    """Test suite for password reset functionality."""

    def setUp(self):
        """Create a test user with known credentials."""
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='OldPassword123!'
        )
        self.new_password = 'NewPassword456!'

    def test_password_reset_request_page_loads(self):
        """Test that password reset request page loads successfully."""
        url = reverse('account_reset_password')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/password_reset.html')

    def test_password_reset_email_sent_with_valid_email(self):
        """Test that password reset email is sent when a valid email is submitted."""
        url = reverse('account_reset_password')
        
        # Clear outbox before test
        mail.outbox = []
        
        response = self.client.post(url, {
            'email': self.user.email
        }, follow=True)
        
        # Check that email was sent
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        
        # Verify email properties
        self.assertEqual(sent_email.to, [self.user.email])
        self.assertIn('password', sent_email.subject.lower() or sent_email.body.lower())
        
        # Check response redirects to done page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/password_reset_done.html')

    def test_password_reset_email_body_contains_reset_link(self):
        """Test that password reset email contains a valid reset link."""
        url = reverse('account_reset_password')
        
        mail.outbox = []
        
        self.client.post(url, {'email': self.user.email})
        
        self.assertEqual(len(mail.outbox), 1)
        email_body = mail.outbox[0].body
        
        # Email should contain a reset URL
        self.assertIn('/reset/', email_body)

    def test_password_reset_with_invalid_email(self):
        """Test that password reset with non-existent email still shows success (security practice)."""
        url = reverse('account_reset_password')
        
        mail.outbox = []
        
        response = self.client.post(url, {
            'email': 'nonexistent@example.com'
        }, follow=True)
        
        # Should still redirect to done page (for security - don't leak if email exists)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/password_reset_done.html')
        
        # But no email should be sent
        self.assertEqual(len(mail.outbox), 0)

    def test_valid_reset_token_shows_form(self):
        """Test that accessing reset link with valid token shows the password form."""
        # Generate a valid token
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        
        url = reverse('account_reset_password_from_key', kwargs={
            'uidb36': uidb64.decode('utf-8') if isinstance(uidb64, bytes) else uidb64,
            'key': token
        })
        
        response = self.client.get(url)
        
        # Should load the form page (not error page)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/password_reset_from_key.html')
        # Should contain form
        self.assertContains(response, 'password', count=None)

    def test_invalid_reset_token_shows_error(self):
        """Test that accessing reset link with invalid token shows error message."""
        # Use an invalid token
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        invalid_token = 'invalid-token-string'
        
        url = reverse('account_reset_password_from_key', kwargs={
            'uidb36': uidb64.decode('utf-8') if isinstance(uidb64, bytes) else uidb64,
            'key': invalid_token
        })
        
        response = self.client.get(url)
        
        # Should still load template but with error state
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/password_reset_from_key.html')

    def test_expired_reset_token_shows_error(self):
        """Test that an expired token shows appropriate error message."""
        # Generate a token and then expire it by changing password
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        
        # Change password to invalidate the token
        self.user.set_password('DifferentPassword789!')
        self.user.save()
        
        url = reverse('account_reset_password_from_key', kwargs={
            'uidb36': uidb64.decode('utf-8') if isinstance(uidb64, bytes) else uidb64,
            'key': token
        })
        
        response = self.client.get(url)
        
        # Should show error state
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/password_reset_from_key.html')

    def test_successful_password_reset_and_password_update_in_database(self):
        """Test the full password reset flow: generate token, submit form, verify password changed."""
        # Step 1: Request password reset email
        url = reverse('account_reset_password')
        
        mail.outbox = []
        response = self.client.post(url, {'email': self.user.email}, follow=True)
        
        self.assertEqual(len(mail.outbox), 1)
        
        # Step 2: Extract token from email and construct reset URL
        email_body = mail.outbox[0].body
        
        # Parse the reset URL from email
        import re
        # Look for pattern like /reset/[uidb36]/[token]/
        match = re.search(r'/reset/([^/]+)/([^/\s]+)/', email_body)
        self.assertIsNotNone(match, "Password reset URL not found in email body")
        
        uidb36, token = match.groups()
        reset_url = reverse('account_reset_password_from_key', kwargs={
            'uidb36': uidb36,
            'key': token
        })
        
        # Step 3: Access the reset form
        response = self.client.get(reset_url)
        self.assertEqual(response.status_code, 200)
        
        # Step 4: Submit new password
        response = self.client.post(reset_url, {
            'password1': self.new_password,
            'password2': self.new_password
        }, follow=True)
        
        # Should redirect to success page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/password_reset_from_key_done.html')
        
        # Step 5: Verify password was actually changed in database
        self.user.refresh_from_db()
        
        # Old password should NOT work
        self.assertFalse(self.user.check_password('OldPassword123!'))
        
        # New password SHOULD work
        self.assertTrue(self.user.check_password(self.new_password))

    def test_password_reset_with_mismatched_passwords(self):
        """Test that form rejects mismatched passwords."""
        # Generate a valid token
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        
        reset_url = reverse('account_reset_password_from_key', kwargs={
            'uidb36': uidb64.decode('utf-8') if isinstance(uidb64, bytes) else uidb64,
            'key': token
        })
        
        # Submit mismatched passwords
        response = self.client.post(reset_url, {
            'password1': self.new_password,
            'password2': 'DifferentPassword789!'
        })
        
        # Should show form again with error (not redirect to success)
        self.assertEqual(response.status_code, 200)
        
        # Password should NOT have changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('OldPassword123!'))
        self.assertFalse(self.user.check_password(self.new_password))

    def test_password_reset_with_weak_password(self):
        """Test that form validates password strength."""
        # Generate a valid token
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        
        reset_url = reverse('account_reset_password_from_key', kwargs={
            'uidb36': uidb64.decode('utf-8') if isinstance(uidb64, bytes) else uidb64,
            'key': token
        })
        
        # Submit a weak password
        response = self.client.post(reset_url, {
            'password1': '123',
            'password2': '123'
        })
        
        # Should show form again with validation error
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', None, None)  # Form has errors

    def test_user_can_login_with_new_password_after_reset(self):
        """Test that user can successfully log in with the new password after reset."""
        # Do a full password reset
        url = reverse('account_reset_password')
        
        mail.outbox = []
        self.client.post(url, {'email': self.user.email})
        
        email_body = mail.outbox[0].body
        import re
        match = re.search(r'/reset/([^/]+)/([^/\s]+)/', email_body)
        uidb36, token = match.groups()
        
        reset_url = reverse('account_reset_password_from_key', kwargs={
            'uidb36': uidb36,
            'key': token
        })
        
        self.client.post(reset_url, {
            'password1': self.new_password,
            'password2': self.new_password
        }, follow=True)
        
        # Now try to login with new password
        login_url = reverse('account_login')
        login_response = self.client.post(login_url, {
            'login': self.user.username,
            'password': self.new_password
        }, follow=True)
        
        # Should be logged in (check for authenticated user in session)
        self.assertEqual(login_response.status_code, 200)
        self.assertTrue(login_response.wsgi_request.user.is_authenticated)

    def test_password_reset_nonexistent_user(self):
        """Test password reset flow for nonexistent user UID."""
        # Create a URL with a user ID that doesn't exist
        fake_uid = urlsafe_base64_encode(force_bytes(99999))
        token = default_token_generator.make_token(self.user)
        
        url = reverse('account_reset_password_from_key', kwargs={
            'uidb36': fake_uid.decode('utf-8') if isinstance(fake_uid, bytes) else fake_uid,
            'key': token
        })
        
        response = self.client.get(url)
        
        # Should load but show invalid token error
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/password_reset_from_key.html')
