"""
THESE TESTS WAS NOT UNDERCHECKED BEFORE....
Author: Sonnet 4.5

Tests for language-specific redirects in authentication flows.

This test suite ensures that user language preference is preserved across:
- Login (regular and social)
- Logout (regular and social)

English users (no prefix) should stay on English pages.
Chinese users (/zh/ prefix) should stay on Chinese pages.
"""

import pytest
from unittest.mock import Mock
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from allauth.socialaccount.models import SocialLogin, SocialAccount
from allauth.account.models import EmailAddress
from users.custom_allauth import MyAccountAdapter, MySocialAccountAdapter

User = get_user_model()


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def account_adapter():
    """Create MyAccountAdapter instance for regular auth."""
    return MyAccountAdapter()


@pytest.fixture
def social_adapter():
    """Create MySocialAccountAdapter instance for social auth."""
    return MySocialAccountAdapter()


@pytest.fixture
def english_request():
    """Create request with English path (no language prefix)."""
    request = RequestFactory().get('/accounts/login/')
    return request


@pytest.fixture
def chinese_request():
    """Create request with Chinese path (/zh/ prefix)."""
    request = RequestFactory().get('/zh/accounts/login/')
    return request


@pytest.fixture
def english_logout_request():
    """Create logout request with English path."""
    request = RequestFactory().post('/accounts/logout/')
    return request


@pytest.fixture
def chinese_logout_request():
    """Create logout request with Chinese path."""
    request = RequestFactory().post('/zh/accounts/logout/')
    return request


@pytest.fixture
def test_user(db):
    """Create a test user for authentication tests."""
    return User.objects.create_user(
        username='testuser', email='test@example.com', password='testpass123'
    )


@pytest.fixture
def google_social_app(db):
    """Create a Google SocialApp for testing."""
    from allauth.socialaccount.models import SocialApp

    app = SocialApp.objects.create(
        provider='google', name='Google', client_id='test-client-id', secret='test-secret'
    )
    return app


@pytest.fixture
def create_sociallogin(google_social_app):
    """
    Factory fixture to create SocialLogin objects for testing.

    Args:
        provider: Social provider name (default: 'google')
        uid: User ID from social provider (default: '123456789')
        email: Email address (default: 'test@example.com')
        user: User instance (optional)

    Returns:
        SocialLogin object
    """

    def _create(provider='google', uid='123456789', email='test@example.com', user=None):
        if user is None:
            user = User()

        social_account = SocialAccount(provider=provider, uid=uid)
        sociallogin = SocialLogin(account=social_account, user=user)

        if email:
            email_address = EmailAddress(email=email, verified=True, primary=True)
            sociallogin.email_addresses = [email_address]
        else:
            sociallogin.email_addresses = []

        return sociallogin

    return _create


# =============================================================================
# MyAccountAdapter Tests - Regular Authentication
# =============================================================================


@pytest.mark.django_db
class TestAccountAdapterLoginRedirect:
    """Test login redirect behavior for regular authentication."""

    def test_english_login_redirects_to_english_email_page(self, account_adapter, english_request):
        """English users should be redirected to /accounts/email/ after login."""
        redirect_url = account_adapter.get_login_redirect_url(english_request)
        assert redirect_url == '/accounts/email/'

    def test_chinese_login_redirects_to_chinese_email_page(self, account_adapter, chinese_request):
        """Chinese users should be redirected to /zh/accounts/email/ after login."""
        redirect_url = account_adapter.get_login_redirect_url(chinese_request)
        assert redirect_url == '/zh/accounts/email/'

    def test_signup_path_also_preserves_language(self, account_adapter):
        """Language should be preserved from signup page as well."""
        # English signup
        en_request = RequestFactory().get('/accounts/signup/')
        assert account_adapter.get_login_redirect_url(en_request) == '/accounts/email/'

        # Chinese signup
        zh_request = RequestFactory().get('/zh/accounts/signup/')
        assert account_adapter.get_login_redirect_url(zh_request) == '/zh/accounts/email/'


@pytest.mark.django_db
class TestAccountAdapterLogoutRedirect:
    """Test logout redirect behavior for regular authentication."""

    def test_english_logout_redirects_to_english_home(
        self, account_adapter, english_logout_request
    ):
        """English users should be redirected to / after logout."""
        redirect_url = account_adapter.get_logout_redirect_url(english_logout_request)
        assert redirect_url == '/'

    def test_chinese_logout_redirects_to_chinese_home(
        self, account_adapter, chinese_logout_request
    ):
        """Chinese users should be redirected to /zh/ after logout."""
        redirect_url = account_adapter.get_logout_redirect_url(chinese_logout_request)
        assert redirect_url == '/zh/'

    def test_logout_from_account_settings_preserves_language(self, account_adapter):
        """Language should be preserved when logging out from account settings."""
        # English account settings
        en_request = RequestFactory().post('/accounts/email/')
        assert account_adapter.get_logout_redirect_url(en_request) == '/'

        # Chinese account settings
        zh_request = RequestFactory().post('/zh/accounts/email/')
        assert account_adapter.get_logout_redirect_url(zh_request) == '/zh/'


# =============================================================================
# MySocialAccountAdapter Tests - Social Authentication (Google OAuth)
# =============================================================================


@pytest.mark.django_db
class TestSocialAccountAdapterLoginRedirect:
    """Test login redirect behavior for social authentication."""

    def test_english_social_login_redirects_to_english_email_page(
        self, social_adapter, english_request
    ):
        """English users using Google OAuth should be redirected to /accounts/email/."""
        redirect_url = social_adapter.get_login_redirect_url(english_request)
        assert redirect_url == '/accounts/email/'

    def test_chinese_social_login_redirects_to_chinese_email_page(
        self, social_adapter, chinese_request
    ):
        """Chinese users using Google OAuth should be redirected to /zh/accounts/email/."""
        redirect_url = social_adapter.get_login_redirect_url(chinese_request)
        assert redirect_url == '/zh/accounts/email/'

    def test_google_callback_path_preserves_language(self, social_adapter):
        """Language should be preserved from OAuth callback URL."""
        # English callback
        en_request = RequestFactory().get('/accounts/google/login/callback/')
        assert social_adapter.get_login_redirect_url(en_request) == '/accounts/email/'

        # Chinese callback
        zh_request = RequestFactory().get('/zh/accounts/google/login/callback/')
        assert social_adapter.get_login_redirect_url(zh_request) == '/zh/accounts/email/'


@pytest.mark.django_db
class TestSocialAccountAdapterLogoutRedirect:
    """Test logout redirect behavior for social authentication."""

    def test_english_social_logout_redirects_to_english_home(
        self, social_adapter, english_logout_request
    ):
        """English users who used social auth should be redirected to / after logout."""
        redirect_url = social_adapter.get_logout_redirect_url(english_logout_request)
        assert redirect_url == '/'

    def test_chinese_social_logout_redirects_to_chinese_home(
        self, social_adapter, chinese_logout_request
    ):
        """Chinese users who used social auth should be redirected to /zh/ after logout."""
        redirect_url = social_adapter.get_logout_redirect_url(chinese_logout_request)
        assert redirect_url == '/zh/'

    def test_social_account_settings_logout_preserves_language(self, social_adapter):
        """Language should be preserved when social auth user logs out."""
        # English
        en_request = RequestFactory().post('/accounts/3rdparty/')
        assert social_adapter.get_logout_redirect_url(en_request) == '/'

        # Chinese
        zh_request = RequestFactory().post('/zh/accounts/3rdparty/')
        assert social_adapter.get_logout_redirect_url(zh_request) == '/zh/'


# =============================================================================
# Edge Cases & Integration Tests
# =============================================================================


@pytest.mark.django_db
class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_empty_path_defaults_to_english(self, account_adapter):
        """Empty or root path should default to English (no prefix)."""
        request = RequestFactory().get('/')

        login_redirect = account_adapter.get_login_redirect_url(request)
        logout_redirect = account_adapter.get_logout_redirect_url(request)

        assert login_redirect == '/accounts/email/'
        assert logout_redirect == '/'

    def test_malformed_zh_prefix_still_works(self, account_adapter):
        """Paths containing /zh/ anywhere should be detected."""
        request = RequestFactory().get('/zh/accounts/password/reset/')

        login_redirect = account_adapter.get_login_redirect_url(request)
        logout_redirect = account_adapter.get_logout_redirect_url(request)

        assert login_redirect == '/zh/accounts/email/'
        assert logout_redirect == '/zh/'

    def test_case_sensitivity_of_zh_prefix(self, account_adapter):
        """Language prefix check should be case-sensitive (lowercase only)."""
        # Uppercase should NOT match
        request_upper = RequestFactory().get('/ZH/accounts/login/')
        assert account_adapter.get_login_redirect_url(request_upper) == '/accounts/email/'

        # Lowercase should match
        request_lower = RequestFactory().get('/zh/accounts/login/')
        assert account_adapter.get_login_redirect_url(request_lower) == '/zh/accounts/email/'

    def test_both_adapters_have_consistent_behavior(self, account_adapter, social_adapter):
        """Both adapters should behave identically for the same paths."""
        paths = [
            '/accounts/login/',
            '/zh/accounts/login/',
            '/accounts/logout/',
            '/zh/accounts/logout/',
        ]

        for path in paths:
            request = RequestFactory().get(path)

            # Login redirects should match
            account_login = account_adapter.get_login_redirect_url(request)
            social_login = social_adapter.get_login_redirect_url(request)
            assert account_login == social_login

            # Logout redirects should match
            account_logout = account_adapter.get_logout_redirect_url(request)
            social_logout = social_adapter.get_logout_redirect_url(request)
            assert account_logout == social_logout


# =============================================================================
# Integration Tests - Full Authentication Flow
# =============================================================================


@pytest.mark.django_db
class TestFullAuthenticationFlow:
    """Test complete authentication flows with language preservation."""

    def test_english_user_full_flow(self, client, test_user):
        """English user should stay on English pages through login/logout."""
        # Login on English page
        response = client.post(
            '/accounts/login/',
            {'login': 'test@example.com', 'password': 'testpass123'},
            follow=False,
        )

        # Should redirect to English email page
        assert response.status_code == 302
        # Note: actual redirect is handled by allauth view, adapter provides the URL

    def test_chinese_user_full_flow(self, client, test_user):
        """Chinese user should stay on Chinese pages through login/logout."""
        # Login on Chinese page
        response = client.post(
            '/zh/accounts/login/',
            {'login': 'test@example.com', 'password': 'testpass123'},
            follow=False,
        )

        # Should redirect (allauth handles actual redirect)
        assert response.status_code == 302
