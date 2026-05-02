from django.conf import settings
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import URLPattern, URLResolver, include, path, re_path

from apps.base.views import IndexView, http_404, http_500
from apps.organizations.views import AcceptInviteView
from config.api import api as ninja_api

# Includes
urlpatterns: list[URLResolver | URLPattern] = [path(r"admin/", admin.site.urls)]

# Project Urls
urlpatterns += [
    path("", login_required(IndexView.as_view()), name="site_index"),
    path("-/", include("django_alive.urls")),
    path("500/", http_500),
    path("404/", http_404),
    path("api/", ninja_api.urls),
    path("_allauth/", include("allauth.headless.urls")),
    path("hijack/", include("hijack.urls")),
    re_path(
        r"^organizations/invite/(?P<key>[0-9a-z]+)/accept/$",
        AcceptInviteView.as_view(),
        name="accept_invite",
    ),
    path("accounts/", include("allauth.urls")),
]

# Debug/Development URLs
if settings.DEBUG is True:
    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
        path("admin/doc/", include("django.contrib.admindocs.urls")),
    ]
