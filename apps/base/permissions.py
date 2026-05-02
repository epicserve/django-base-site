"""
Permission helpers for ninja routes.

These replace DRF's permission_classes with a small set of explicit checks
that raise ``PermissionDenied`` (which the global error handler in
apps/base/errors.py converts to a 403 with a ``{detail: ...}`` body).
"""

from collections.abc import Callable
from typing import Any

from django.core.exceptions import PermissionDenied
from django.http import HttpRequest

SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


def require_authenticated(request: HttpRequest) -> None:
    if not (request.user and request.user.is_authenticated):
        raise PermissionDenied("Authentication required.")


def require_superuser(request: HttpRequest) -> None:
    require_authenticated(request)
    if not request.user.is_superuser:
        raise PermissionDenied("Superuser permission required.")


def require_org_selected(request: HttpRequest) -> Any:
    """Return the active organization model instance or raise 403."""
    org_ctx = getattr(request, "org", None)
    org = org_ctx.instance if org_ctx is not None else None
    if org is None:
        raise PermissionDenied("Make sure you've selected an organization first.")
    return org


def require_org_owner(request: HttpRequest) -> Any:
    """Return the active org or raise 403 if the user isn't the owner."""
    org = require_org_selected(request)
    if not org.is_owner(request.user):
        raise PermissionDenied("Only organization owners are allowed to perform this action.")
    return org


def check_owner_or_member(request: HttpRequest, obj, *, allow_safe_methods: bool = True) -> None:
    """
    Object-level check matching the old IsOwnerOrReadOnly.

    - Safe methods (GET/HEAD/OPTIONS) are allowed when ``allow_safe_methods`` is True.
    - Otherwise the object's owning user must be the requester, or the requester
      must be a member of the object's organization (with the request org matching
      the object's org).

    Apply inside the route after fetching the object.
    """
    if allow_safe_methods and request.method in SAFE_METHODS:
        return

    obj_org = getattr(obj, "organization", None)
    if obj_org is None:
        project = getattr(obj, "project", None)
        if project is not None:
            obj_org = project.organization

    request_org_ctx = getattr(request, "org", None)
    request_org_id = request_org_ctx.id if request_org_ctx is not None else None

    if obj_org is not None and request_org_id is not None and obj_org.id != request_org_id:
        raise PermissionDenied("This object belongs to a different organization.")

    obj_user = getattr(obj, "user", None)
    if obj_user is not None and obj_user == request.user:
        return

    org_instance = request_org_ctx.instance if request_org_ctx is not None and request_org_ctx.id else None
    if org_instance and org_instance.is_member(request.user):
        return

    raise PermissionDenied("You don't have permission to modify this object.")


def org_owner_only(view_fn: Callable) -> Callable:
    """Wrap a route function with the ``require_org_owner`` check."""

    def wrapper(request, *args, **kwargs):
        require_org_owner(request)
        return view_fn(request, *args, **kwargs)

    wrapper.__name__ = view_fn.__name__
    wrapper.__doc__ = view_fn.__doc__
    return wrapper
