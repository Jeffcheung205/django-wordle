# though different parts of cutomization should be put in different files
# make things start here first

import json
import logging
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

# Set up logger
logger = logging.getLogger(__name__)


class MyAccountAdapter(DefaultAccountAdapter):
    """Adapter for regular username/password authentication."""

    # this is overriding, better lookup the super class implmentation first
    def get_login_redirect_url(self, request):
        """Override redirect after regular login."""
        return '/accounts/email/'


class MySocialAccountAdapter(DefaultSocialAccountAdapter):

    def pre_social_login(self, request, sociallogin):
        provider = sociallogin.account.provider

        # Log to Django logger as well
        email = sociallogin.email_addresses[0].email if sociallogin.email_addresses else 'None'
        logger.info(
            f'Social login callback from {provider}: '
            f'uid={sociallogin.account.uid}, '
            f'email={email}, '
            f'is_existing={sociallogin.is_existing}'
        )

        return super().pre_social_login(request, sociallogin)

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)

        if sociallogin.account.provider == 'google':
            user.first_name = data.get('given_name', '')
            user.last_name = data.get('family_name', '')

        return user

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)

        # You could do additional things here:
        # - Create user profile
        # - Send welcome email
        # - Log analytics event
        # - etc.

        return user

    def get_login_redirect_url(self, request):
        # social_accounts = request.user.socialaccount_set.all()
        return '/accounts/email/'

    def is_auto_signup_allowed(self, request, sociallogin):
        """
        Control whether auto signup is allowed.
        Return False to force user through signup form.
        """
        # You could add logic here, for example:
        # - Only allow auto-signup for verified emails
        # - Require additional info for certain providers
        # - Check if email domain is whitelisted

        return True

    def authentication_error(
        self, request, provider_id, error=None, exception=None, extra_context=None
    ):
        """
        Handle authentication errors from social providers.
        """
        # Log error
        logger.error(
            f'Social auth error from {provider_id}: {error}',
            exc_info=exception,
            extra={'extra_context': extra_context},
        )
        return super().authentication_error(request, provider_id, error, exception, extra_context)
