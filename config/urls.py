from django.conf import settings
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import URLPattern, URLResolver, include, path
from django.views.generic import TemplateView

from apps.accounts.views import NameChange, SignInView
from apps.base.views import http_404, http_500

# Includes
urlpatterns: list[URLResolver | URLPattern] = [path(r"admin/", admin.site.urls)]

# Project Urls
urlpatterns += [
    path("", login_required(TemplateView.as_view(template_name="index.html")), name="site_index"),
    path("-/", include("django_alive.urls")),
    path("500/", http_500),
    path("404/", http_404),
    path("accounts/name/", NameChange.as_view(), name="account_change_name"),
    path("accounts/login/", SignInView.as_view(), name="account_login"),
    path("accounts/", include("allauth.urls")),
]

# Debug/Development URLs
if settings.DEBUG is True:
    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
        path("admin/doc/", include("django.contrib.admindocs.urls")),
    ]
