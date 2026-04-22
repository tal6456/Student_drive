"""
Accessibility Widget Refactoring Verification
==============================================

Core tests to verify the refactored a11y-floating-widget follows Good Citizen patterns:
1. Semantic HTML (nav element, proper ARIA attributes)
2. No excessive !important overrides
3. CSS variables usage (--gd-border, --gd-card, etc.)
4. Logical properties (inset-block-end, inset-inline-end)
5. Inherited directionality (no dir="rtl" on widget)
"""

from django.test.client import Client
from django.test import RequestFactory
from django.template.loader import render_to_string
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.tests.base import BaseTestCase

User = get_user_model()


class AccessibilityWidgetRefactoringTests(BaseTestCase):
    """Test that the refactored widget follows Good Citizen patterns."""

    def setUp(self):
        super().setUp()
        self.client = Client()
        self.factory = RequestFactory()
        # Create test user with profile
        self.user = User.objects.create_user(
            username='a11ytest',
            email='a11ytest@example.com',
            password='testpass123',
            first_name='A11y',
            last_name='Tester'
        )
        from core.models import UserProfile
        UserProfile.objects.get_or_create(
            user=self.user,
            defaults={'phone_number': '0501234567'}
        )

    def _get_rendered_base_template(self):
        """Helper to get the base.html template rendered for an authenticated user."""
        # Render the base template directly with the user context
        context = {
            'user': self.user,
            'unread_notifications_count': 0,
        }
        return render_to_string('core/base.html', context)

    def test_widget_uses_semantic_nav_element(self):
        """✓ VERIFY: Widget is a semantic <nav> element, not a <div>."""
        content = self._get_rendered_base_template()
        self.assertIn('<nav id="a11y-floating-widget"', content)

    def test_widget_has_proper_aria_attributes(self):
        """✓ VERIFY: Widget has proper ARIA labels and controls."""
        content = self._get_rendered_base_template()
        self.assertIn('aria-label="תפריט נגישות"', content)
        self.assertIn('aria-controls="a11y-menu"', content)
        self.assertIn('aria-expanded="false"', content)

    def test_widget_inherits_directionality(self):
        """✓ VERIFY: Widget does NOT force dir="rtl", inherits from body."""
        content = self._get_rendered_base_template()
        # Should have the widget WITHOUT dir="rtl" attribute
        nav_idx = content.find('<nav id="a11y-floating-widget"')
        self.assertGreater(nav_idx, -1, "Widget nav element not found")
        # Extract the nav opening tag
        nav_closing_bracket = content.find('>', nav_idx)
        nav_opening = content[nav_idx:nav_closing_bracket]
        # Should NOT have dir="rtl" attribute on the widget
        self.assertNotIn('dir="rtl"', nav_opening)
        # But should have the inheritance comment
        self.assertIn('Inherits dir="rtl" from <body>', content)

    def test_widget_css_uses_variables_not_hardcoded(self):
        """✓ VERIFY: CSS uses --gd-* variables instead of hard-coded colors."""
        content = self._get_rendered_base_template()
        # Should use CSS variables
        self.assertIn('var(--gd-border)', content)
        self.assertIn('var(--gd-card)', content)
        self.assertIn('var(--gd-text)', content)
        self.assertIn('var(--gd-bg)', content)
        self.assertIn('var(--gd-hover-bg)', content)
        self.assertIn('var(--gd-primary)', content)

    def test_widget_css_has_zero_important_overrides(self):
        """✓ VERIFY: Widget CSS does NOT use !important tags."""
        content = self._get_rendered_base_template()
        # Find the widget CSS section
        css_start = content.find('/* === Accessibility Widget')
        css_end = content.find('#main-content', css_start)
        if css_start > -1 and css_end > -1:
            widget_css = content[css_start:css_end]
            important_count = widget_css.count('!important')
            self.assertEqual(important_count, 0,
                           f"Widget CSS should have 0 !important, found {important_count}")

    def test_widget_uses_logical_properties(self):
        """✓ VERIFY: CSS uses logical properties (inset-block-end, inset-inline-end)."""
        content = self._get_rendered_base_template()
        # Should use logical properties for RTL compatibility
        self.assertIn('inset-block-end:', content)
        self.assertIn('inset-inline-end:', content)
        # Should NOT use old-style left/right positioning in widget
        css_start = content.find('/* === Accessibility Widget')
        css_end = content.find('#main-content', css_start)
        if css_start > -1 and css_end > -1:
            widget_css = content[css_start:css_end]
            # left: and right: should not appear in the widget CSS
            self.assertNotIn('left:', widget_css)
            self.assertNotIn('right:', widget_css)

    def test_widget_menu_items_have_proper_roles(self):
        """✓ VERIFY: Menu items have proper ARIA menuitem roles."""
        content = self._get_rendered_base_template()
        # Should have 5 menu items with role="menuitem"
        menuitem_count = content.count('role="menuitem"')
        self.assertEqual(menuitem_count, 5, 
                        f"Should have 5 menuitem roles, found {menuitem_count}")

    def test_widget_icons_are_aria_hidden(self):
        """✓ VERIFY: Icons have aria-hidden="true" for accessibility."""
        content = self._get_rendered_base_template()
        # Should have multiple aria-hidden="true" (one per icon)
        aria_hidden_count = content.count('aria-hidden="true"')
        self.assertGreaterEqual(aria_hidden_count, 5,
                               f"Should have at least 5 aria-hidden icons, found {aria_hidden_count}")

    def test_widget_uses_bootstrap_d_none_utility(self):
        """✓ VERIFY: Widget menu uses Bootstrap d-none class for hiding."""
        content = self._get_rendered_base_template()
        self.assertIn('id="a11y-menu" class="d-none"', content)

    def test_widget_has_no_forced_text_align_right(self):
        """✓ VERIFY: Widget doesn't force text-align: right !important."""
        content = self._get_rendered_base_template()
        css_start = content.find('/* === Accessibility Widget')
        css_end = content.find('#main-content', css_start)
        if css_start > -1 and css_end > -1:
            widget_css = content[css_start:css_end]
            # Should not have text-align: right !important
            self.assertNotIn('text-align: right !important', widget_css)

    def test_widget_buttons_have_semantic_structure(self):
        """✓ VERIFY: Control buttons are properly structured with icon + text."""
        content = self._get_rendered_base_template()
        # Should have buttons with icon and span structure
        self.assertIn('<i class="fas fa-plus" aria-hidden="true"></i>', content)
        self.assertIn('<span>הגדל טקסט</span>', content)
        # All buttons should have the a11y-control-btn class
        control_btn_count = content.count('class="a11y-control-btn"')
        self.assertEqual(control_btn_count, 5,
                        f"Should have 5 control buttons, found {control_btn_count}")
