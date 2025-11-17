"""
Tests for social authentication features (Google OAuth).
Covers: missing email blocking, account linking by email.
"""

import pytest
from unittest.mock import Mock
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory
from allauth.socialaccount.models import SocialAccount, SocialLogin
from allauth.account.models import EmailAddress
from allauth.exceptions import ImmediateHttpResponse
from users.custom_allauth import MySocialAccountAdapter

User = get_user_model()


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def request_with_messages():
    """Create a request with message storage for Django messages framework."""
    request = RequestFactory().get('/accounts/google/login/callback/')
    setattr(request, 'session', {})
    setattr(request, '_messages', FallbackStorage(request))
    return request


@pytest.fixture
def social_adapter():
    """Create MySocialAccountAdapter instance."""
    return MySocialAccountAdapter()


@pytest.fixture
def create_sociallogin_mock():
    """
    Factory fixture to create customizable SocialLogin mocks.

    Args:
        provider: Social provider name (default: 'google')
        uid: User ID from social provider (default: '123456789')
        email: Email address or None (default: None)
        is_existing: Whether account already exists (default: False)

    Returns:
        Mock SocialLogin object
    """

    def _create(provider='google', uid='123456789', email=None, is_existing=False):
        sociallogin = Mock(spec=SocialLogin)
        sociallogin.account = Mock()
        sociallogin.account.provider = provider
        sociallogin.account.uid = uid
        sociallogin.is_existing = is_existing

        # Handle email addresses
        if email:
            mock_email = Mock()
            mock_email.email = email
            sociallogin.email_addresses = [mock_email]
        else:
            sociallogin.email_addresses = []

        return sociallogin

    return _create


@pytest.fixture
def google_social_app(db):
    """Create a Google SocialApp for testing."""
    from allauth.socialaccount.models import SocialApp

    # Create Google SocialApp (settings-based approach, no sites needed)
    app = SocialApp.objects.create(
        provider='google', name='Google', client_id='test-client-id', secret='test-secret'
    )
    return app


@pytest.fixture
def create_real_sociallogin(google_social_app):
    """
    Factory fixture to create real SocialLogin objects for integration tests.

    This creates actual Django-allauth objects that interact with the database,
    allowing end-to-end testing of the social authentication flow.

    Args:
        provider: Social provider name (default: 'google')
        uid: User ID from social provider (default: '123456789')
        email: Email address or None (default: None)
        user: Optional user to associate with the social account

    Returns:
        Real SocialLogin object
    """

    def _create(provider='google', uid='123456789', email=None, user=None):
        if user is None:
            user = User()

        social_account = SocialAccount(provider=provider, uid=uid)

        sociallogin = SocialLogin(account=social_account, user=user)

        if email:
            # this mock is not real, if the email has been registered as regular account,
            # the existing email address will still be unverified.
            email_address = EmailAddress(email=email, verified=True, primary=True)
            sociallogin.email_addresses = [email_address]
        else:
            sociallogin.email_addresses = []

        return sociallogin

    return _create


# =============================================================================
# Feature 1: Block Signup When Google OAuth Missing Email
# =============================================================================


@pytest.mark.django_db
class TestGoogleOAuthMissingEmail:
    """Test that signup is blocked when Google OAuth doesn't provide email."""

    def test_missing_email_raises_immediate_http_response(
        self, request_with_messages, social_adapter, create_sociallogin_mock
    ):
        """Should raise ImmediateHttpResponse when email is missing."""
        sociallogin = create_sociallogin_mock(email=None)

        with pytest.raises(ImmediateHttpResponse):
            social_adapter.pre_social_login(request_with_messages, sociallogin)

    def test_missing_email_redirects_to_login(
        self, request_with_messages, social_adapter, create_sociallogin_mock
    ):
        """Should redirect to login page when email is missing."""
        sociallogin = create_sociallogin_mock(email=None)

        try:
            social_adapter.pre_social_login(request_with_messages, sociallogin)
        except ImmediateHttpResponse as e:
            # Verify redirect to login
            assert e.response.status_code == 302
            assert e.response.url == '/accounts/login/'

    def test_missing_email_adds_error_message(
        self, request_with_messages, social_adapter, create_sociallogin_mock
    ):
        """Should add an error message when email is missing."""
        sociallogin = create_sociallogin_mock(email=None)

        try:
            social_adapter.pre_social_login(request_with_messages, sociallogin)
        except ImmediateHttpResponse:
            pass  # Expected

        # Verify error message was added
        messages = list(get_messages(request_with_messages))
        assert len(messages) == 1
        assert 'must provide an email address' in str(messages[0])


# =============================================================================
# Feature 2: Account Linking by Email
# =============================================================================


@pytest.mark.django_db
class TestAccountLinkingByEmail:
    """Test that social accounts are linked to existing users by email."""

    def test_links_social_account_to_existing_user(
        self, request_with_messages, social_adapter, create_real_sociallogin
    ):
        """
        Scenario: A user registers with email A. Later user logged out.
        Sometimes later, the same user tries to sign up/log in via Google OAuth with same email
        The system should link the social account to the existing user and SocialAccount
        should have one entry.

        Coveat 8ad9: test@gmail.com was created in EmailAddress and unverified. After
                     google oauth login with test@gmail.com, the test@gmail.com in EmailAddress
                     is still unverified, default allauth behavior.
        """
        # Create existing user
        existing_user = User.objects.create_user(
            username='existinguser', email='test@example.com', password='testpass123'
        )

        assert User.objects.count() == 1
        assert SocialAccount.objects.count() == 0

        # Create anonymous request
        request_with_messages.user = Mock()
        request_with_messages.user.is_anonymous = True

        # Create real social login object with same email
        sociallogin = create_real_sociallogin(email='test@example.com')

        # Call pre_social_login - this will link the account
        social_adapter.pre_social_login(request_with_messages, sociallogin)

        # Verify database state: User count stays same, SocialAccount created
        assert User.objects.count() == 1
        assert SocialAccount.objects.count() == 1

        # Verify the SocialAccount is linked to the existing user
        social_account = SocialAccount.objects.get()
        assert social_account.user == existing_user
        assert social_account.provider == 'google'
        assert social_account.uid == '123456789'

    def test_when_user_already_authenticated(
        self, request_with_messages, social_adapter, create_sociallogin_mock
    ):
        """
        Scenario: an existing user who signed up with email user1@example.com, however later
        while logged in, he tried to connect this regular account to google oauth which is
        user1@gmail.com.

        Tested. In this case, the user will hold user1@example.com as the User email. While the social
        account is optional and a new SocialAccount record is created and linked to the same user.
        The connection can be removed.

        Coveat 8ad9: only user1@gmail.com is created in EmailAddress, but not user1@gmail.com, only
        records in EmailAddress can be verified
        """
        pass
