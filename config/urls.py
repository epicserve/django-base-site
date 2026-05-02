from django.conf import settings
from django.contrib import admin
from django.http import HttpResponseNotFound
from django.urls import URLPattern, URLResolver, include, path, re_path

from apps.base.views import SPAView, http_404, http_500, qr_svg
from config.api import api as ninja_api


def _public_not_found(request, path=""):
    """
    Catch missing /public/static/* (stale Vite chunks during a deploy) and
    /public/media/* requests so the SPA catch-all doesn't answer 200 with
    HTML for a missing asset (which would break dynamic-import chunk loads).
    """
    return HttpResponseNotFound()


urlpatterns: list[URLResolver | URLPattern] = [
    path("_allauth/", include("allauth.headless.urls")),
    path("api/", ninja_api.urls),
    path("-/", include("django_alive.urls")),
    path("admin/", admin.site.urls),
    path("hijack/", include("hijack.urls")),
    path("500/", http_500),
    path("404/", http_404),
    path("qr/", qr_svg, name="qr-svg"),
    # Keep the URL name so OrganizationInvite.accept_invite_url's reverse() and
    # email links still resolve, but render the SPA shell so the Vue route at
    # /organizations/invite/:key/accept/ handles the flow.
    re_path(
        r"^organizations/invite/(?P<key>[0-9a-z]+)/accept/$",
        SPAView.as_view(),
        name="accept_invite",
    ),
    re_path(r"^public/", _public_not_found, name="public-not-found"),
    re_path(r"^(?!public/).*$", SPAView.as_view(), name="spa"),
]

if settings.DEBUG is True:
    import debug_toolbar

    urlpatterns.insert(0, path("__debug__/", include(debug_toolbar.urls)))
    urlpatterns.insert(1, path("admin/doc/", include("django.contrib.admindocs.urls")))
