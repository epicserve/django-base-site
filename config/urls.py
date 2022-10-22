from typing import Union

from django.conf import settings
from django.contrib import admin
from django.urls import URLPattern, URLResolver, include, path
from django.views.generic import TemplateView

from apps.base.views import NameChange, http_404, http_500

# Includes
urlpatterns: list[Union[URLResolver, URLPattern]] = [path(r"admin/", admin.site.urls)]

# Project Urls
urlpatterns += [
    path("", TemplateView.as_view(template_name="index.html"), name="site_index"),
    path("500/", http_500),
    path("404/", http_404),
    path("accounts/name/", NameChange.as_view(), name="account_change_name"),
    path("accounts/", include("allauth.urls")),
]

# Debug/Development URLs
if settings.DEBUG is True:
    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
        path("admin/doc/", include("django.contrib.admindocs.urls")),
    ]
