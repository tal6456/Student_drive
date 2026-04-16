"""
What is this file for?
----------------------
This file acts as a traffic controller for the Allauth authentication flow,
deciding where to send the user immediately after authentication.

It handles:
1. New user routing: sends fresh signups directly to the profile completion page.
2. Profile readiness checks: applies smart logic on each login to see whether
   the user is missing critical details (such as a first name) and routes them accordingly.
3. Social login integration: aligns the Google signup flow with the regular
   signup flow so data collection behaves the same way.
"""

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.urls import reverse


class CustomAccountAdapter(DefaultAccountAdapter):
    def get_signup_redirect_url(self, request):
        # Runs only when a new user signs up with email and password for the first time
        return reverse('complete_profile')

    def get_login_redirect_url(self, request):
        # Runs on every login, whether regular or an automatic Google connection to an existing user
        user = request.user

        # Smart logic: check whether the profile is missing basic details (for example, first name)
        # If there is no first name, the user never finished the "complete profile" form
        if not user.first_name:
            return reverse('complete_profile')

        # If everything is filled in, send them to the home page
        return reverse('home')


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def get_signup_redirect_url(self, request, sociallogin):
        # Runs only when a new user signs up via Google for the first time
        return reverse('complete_profile')
