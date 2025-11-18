import re
import logging
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

logger = logging.getLogger(__name__)
from django.contrib.auth import get_user_model

User = get_user_model()


def generate_username_from_email(user):
    from allauth.account.utils import user_username, user_email

    username = user_username(user)

    if not username:
        email = user_email(user)
        if email:
            local_part = email.split('@')[0]
            base_username = re.sub(r'[^\w]', '_', local_part)[:150]

            username = base_username
            counter = 1
            while User.objects.filter(username=username).exclude(pk=user.pk).exists():
                username = f'{base_username}_{counter}'
                counter += 1

            user_username(user, username)


class MyAccountAdapter(DefaultAccountAdapter):
    """Adapter for regular username/password authentication."""

    def get_login_redirect_url(self, request):
        """Override redirect after regular login."""
        if request.path.startswith('/zh/'):
            return '/zh/accounts/email/'
        return '/accounts/email/'

    def get_logout_redirect_url(self, request):
        """Override redirect after logout to preserve language."""
        if request.path.startswith('/zh/'):
            return '/zh/'
        return '/'

    def populate_username(self, request, user):
        generate_username_from_email(user)


class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        Link social account to existing user with same email.
        Block signup if email is missing from social provider.
        """
        provider = sociallogin.account.provider

        # Extract email
        email = sociallogin.email_addresses[0].email if sociallogin.email_addresses else None

        # Log social login attempt
        logger.info(
            f'Social login callback from {provider}: '
            f'uid={sociallogin.account.uid}, '
            f'email={email}, '
            f'is_existing={sociallogin.is_existing}'
        )

        if not email:
            logger.error(f'Social login from {provider} missing email - blocking signup')
            from django.contrib import messages
            from allauth.exceptions import ImmediateHttpResponse
            from django.shortcuts import redirect

            messages.error(
                request,
                f'Your {provider.title()} account must provide an email address to sign up. '
                f'Please check your {provider.title()} account settings.',
            )
            raise ImmediateHttpResponse(redirect('/accounts/login/'))

        if not sociallogin.is_existing and request.user.is_anonymous:
            try:
                user = User.objects.get(email=email)

                sociallogin.connect(request, user)
                logger.info(f'Linked {provider} account to existing user: {email}')
            except User.DoesNotExist:
                logger.info(f'New user signup from {provider}: {email}')
            except User.MultipleObjectsReturned:
                logger.error(f'Multiple users found with email: {email}')
        return super().pre_social_login(request, sociallogin)

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)

        if sociallogin.account.provider == 'google':
            user.first_name = data.get('given_name', '')
            user.last_name = data.get('family_name', '')

        return user

    def populate_username(self, request, user):
        generate_username_from_email(user)

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)

        # You could do additional things here:
        # - Create user profile
        # - Send welcome email
        # - Log analytics event
        # - etc.

        return user

    def get_login_redirect_url(self, request):
        """Override redirect after social login."""
        if request.path.startswith('/zh/'):
            return '/zh/accounts/email/'
        return '/accounts/email/'

    def get_logout_redirect_url(self, request):
        """Override redirect after logout to preserve language."""
        if request.path.startswith('/zh/'):
            return '/zh/'
        return '/'

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
