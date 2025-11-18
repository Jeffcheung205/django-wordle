"""
URL configuration for christmax project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import include
from django.urls import path
from django.views.i18n import JavaScriptCatalog
from django.views.generic import TemplateView

from base.views import HomeView

urlpatterns = [
    path('admin/', admin.site.urls),
    # Django-allauth URLs (outside i18n_patterns to avoid duplicate registration)
]

urlpatterns += i18n_patterns(
    path('jsi18n/', JavaScriptCatalog.as_view(packages=['base']), name='javascript-catalog'),
    path('', HomeView.as_view(), name='home'),
    path('', HomeView.as_view(), name='home_zh'),
    path('accounts/', include('allauth.urls')),
    # require login or redirect to login page
    # path('accounts/profile/', TemplateView.as_view(template_name="profile.html"), name='profile'),
    prefix_default_language=False,
)

if settings.DEBUG:
  if "debug_toolbar" in settings.INSTALLED_APPS:
      import debug_toolbar
      urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
