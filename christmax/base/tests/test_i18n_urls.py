"""URL-level tests for i18n-aware homepage routes."""
from django.urls import resolve
from django.urls import Resolver404
from django.urls import reverse
from django.utils.translation import override


def _resolved_home_path(path: str, client):
    try:
        match = resolve(path)
    except Resolver404:
        match = client.get(path).resolver_match
    view_class = getattr(match.func, 'view_class', None)
    return f'{view_class.__module__}.{view_class.__name__}'


def test_english_url_resolves(client):
    """The root path should resolve to the English home view."""
    assert reverse('home') == '/'
    assert _resolved_home_path('/', client) == 'base.views.HomeView'


def test_chinese_url_resolves(client):
    """The /zh/ path should resolve to the same view."""
    with override('zh'):
        assert reverse('home_zh') == '/zh/'
    assert _resolved_home_path('/zh/', client) == 'base.views.HomeView'


def test_url_name_conflicts():
    """English and Chinese URL names should map to different paths."""
    with override('en'):
        english_url = reverse('home')
    with override('zh'):
        chinese_url = reverse('home_zh')
    assert english_url != chinese_url
