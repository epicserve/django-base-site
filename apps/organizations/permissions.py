"""
Organization permission checks for ninja routes.

Like the helpers in apps/base/permissions.py, these raise ``PermissionDenied``, which the global error handler in
apps/base/errors.py converts to a 403 with a ``{detail: ...}`` body.
"""

from typing import Any

from django.core.exceptions import PermissionDenied
from django.http import HttpRequest

from apps.organizations.roles import OrgPerm, has_org_perm


def require_org_selected(request: HttpRequest) -> Any:
    """Return the active organization model instance or raise 403."""
    org_ctx = getattr(request, "org", None)
    org = org_ctx.instance if org_ctx is not None else None
    if org is None:
        raise PermissionDenied("Make sure you've selected an organization first.")
    return org


def require_org_perm(request: HttpRequest, perm: OrgPerm) -> Any:
    """Return the active org, or raise 403 if the user's role in it doesn't grant the permission."""
    org = require_org_selected(request)
    if not has_org_perm(request.user, org, perm):
        raise PermissionDenied("Your role in this organization doesn't allow this.")
    return org
