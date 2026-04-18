import re

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp


@override_settings(
    STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage',
    STORAGES={
        'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
        'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
    },
)
class AccessibilityTemplateTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='a11y_user',
            email='a11y@example.com',
            password='StrongPass123!'
        )
        self.user.first_name = 'נגיש'
        self.user.save(update_fields=['first_name'])

        profile = self.user.profile
        profile.phone_number = '0501234567'
        profile.save()

        site = Site.objects.get_current()
        social_app = SocialApp.objects.create(
            provider='google',
            name='Google',
            client_id='test-google-client-id',
            secret='test-google-secret'
        )
        social_app.sites.add(site)

    def _count_tag(self, html, tag_name):
        return len(re.findall(rf'<{tag_name}(\s|>)', html, flags=re.IGNORECASE))

    def _extract_input_ids_requiring_labels(self, html):
        input_tags = re.findall(r'<input\b[^>]*>', html, flags=re.IGNORECASE)
        ids = []

        for input_tag in input_tags:
            type_match = re.search(r'type=["\']([^"\']+)["\']', input_tag, flags=re.IGNORECASE)
            id_match = re.search(r'id=["\']([^"\']+)["\']', input_tag, flags=re.IGNORECASE)

            input_type = (type_match.group(1).lower() if type_match else 'text')
            if input_type in {'hidden', 'submit', 'button'}:
                continue
            if not id_match:
                continue
            ids.append(id_match.group(1))

        return ids

    def test_skip_to_content_link_exists_and_points_to_main_id(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'href="#main-content"', html=False)
        self.assertContains(response, 'id="main-content"', html=False)

    def test_key_nav_icon_controls_have_hebrew_aria_labels(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'aria-label="התראות"', html=False)
        self.assertContains(response, 'aria-label="פתח תפריט ניווט"', html=False)
        self.assertContains(response, 'aria-label="פרופיל משתמש"', html=False)

    def test_login_and_password_reset_inputs_have_matching_labels(self):
        for url_name in ['account_login', 'account_reset_password']:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 200)
            html = response.content.decode('utf-8')

            input_ids = self._extract_input_ids_requiring_labels(html)
            input_ids = [
                input_id for input_id in input_ids
                if input_id not in {'navbarSearchInput', 'invite-link-input'}
            ]
            self.assertGreater(len(input_ids), 0)

            for input_id in input_ids:
                self.assertRegex(
                    html,
                    rf'<label[^>]*for=["\']{re.escape(input_id)}["\'][^>]*>',
                    msg=f'Input with id "{input_id}" on {url_name} is missing a matching label.'
                )

    def test_major_pages_have_single_h1_and_nav_main_landmarks(self):
        major_pages = [
            (reverse('accessibility'), False),
        ]

        for page, requires_auth in major_pages:
            if requires_auth:
                self.client.force_login(self.user)
            else:
                self.client.logout()

            response = self.client.get(page, follow=True)
            self.assertEqual(response.status_code, 200)
            html = response.content.decode('utf-8')

            self.assertEqual(self._count_tag(html, 'h1'), 1, msg=f'Expected exactly one h1 in {page}')
            self.assertGreaterEqual(self._count_tag(html, 'nav'), 1, msg=f'Expected at least one nav in {page}')
            self.assertGreaterEqual(self._count_tag(html, 'main'), 1, msg=f'Expected at least one main in {page}')

    def test_accessibility_page_exists(self):
        response = self.client.get(reverse('accessibility'))
        self.assertEqual(response.status_code, 200)
