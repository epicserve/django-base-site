from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject

from apps.organizations.session import get_organization


def _get_organization(request):
    request._cached_organization = getattr(request, "_cached_organization", None)
    if not request._cached_organization:
        request._cached_organization = get_organization(request)
    return request._cached_organization


class OrganizationMiddleware(MiddlewareMixin):
    @staticmethod
    def process_request(request):
        assert hasattr(request, "session"), (  # noqa: S101
            "The Django authentication middleware requires session middleware "
            "to be installed. Edit your MIDDLEWARE setting to insert "
            "'django.contrib.sessions.middleware.SessionMiddleware' before "
            "'django.contrib.auth.middleware.AuthenticationMiddleware'."
        )
        request.org = SimpleLazyObject(lambda: _get_organization(request))
