"""
Permission helpers for ninja routes.

These replace DRF's permission_classes with a small set of explicit checks
that raise ``PermissionDenied`` (which the global error handler in
apps/base/errors.py converts to a 403 with a ``{detail: ...}`` body).

The organization checks (``require_org_selected``, ``require_org_perm``) live in
apps/organizations/permissions.py, next to the roles they check.
"""

from django.core.exceptions import PermissionDenied
from django.http import HttpRequest


def require_authenticated(request: HttpRequest) -> None:
    if not (request.user and request.user.is_authenticated):
        raise PermissionDenied("Authentication required.")


def require_superuser(request: HttpRequest) -> None:
    require_authenticated(request)
    if not getattr(request.user, "is_superuser", False):
        raise PermissionDenied("Superuser permission required.")
