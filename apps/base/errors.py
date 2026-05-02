"""
Exception handlers for the ninja API.

Translate ninja/Pydantic/Django errors into the DRF-style
``{field: [messages, ...]}`` envelope the Vue SPA's parseErrors
helper (see src/js/utils/api.js) already understands.
"""

from collections import defaultdict

from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404, JsonResponse

from ninja.errors import HttpError
from ninja.errors import ValidationError as NinjaValidationError


def _wrap_field_errors(field_errors: dict[str, list[str]]) -> dict[str, list[str]]:
    return {field: list(messages) for field, messages in field_errors.items() if messages}


def _ninja_validation_to_field_errors(exc: NinjaValidationError) -> dict[str, list[str]]:
    """
    Translate ninja validation errors into a field-keyed dict.

    Ninja emits ``[{loc: [...], msg: ..., type: ...}, ...]``; this collapses
    that into ``{field_name: [msg, ...]}``. The last meaningful element of
    ``loc`` is the field name; ``body``/``query``/``path`` location prefixes
    are dropped.
    """
    grouped: dict[str, list[str]] = defaultdict(list)
    for err in exc.errors:
        loc = [str(part) for part in err.get("loc", []) if str(part) not in {"body", "query", "path", "form"}]
        field = loc[-1] if loc else "non_field_errors"
        grouped[field].append(err.get("msg", "Invalid input."))
    return _wrap_field_errors(grouped)


def _django_validation_to_field_errors(exc: DjangoValidationError) -> dict[str, list[str]]:
    if hasattr(exc, "message_dict"):
        # Replace the magic __all__ key with the SPA's expected non_field_errors key.
        result = dict(exc.message_dict)
        if "__all__" in result:
            result["non_field_errors"] = result.pop("__all__")
        return _wrap_field_errors(result)
    if hasattr(exc, "messages"):
        return _wrap_field_errors({"non_field_errors": list(exc.messages)})
    return _wrap_field_errors({"non_field_errors": [str(exc)]})


def register_error_handlers(api) -> None:
    @api.exception_handler(NinjaValidationError)
    def _ninja_validation(request, exc):
        return JsonResponse(_ninja_validation_to_field_errors(exc), status=400)

    @api.exception_handler(DjangoValidationError)
    def _django_validation(request, exc):
        return JsonResponse(_django_validation_to_field_errors(exc), status=400)

    @api.exception_handler(PermissionDenied)
    def _permission_denied(request, exc):
        return JsonResponse({"detail": str(exc) or "Permission denied."}, status=403)

    @api.exception_handler(Http404)
    def _not_found(request, exc):
        return JsonResponse({"detail": "Not found."}, status=404)

    @api.exception_handler(HttpError)
    def _http_error(request, exc):
        return JsonResponse({"detail": exc.message}, status=exc.status_code)
