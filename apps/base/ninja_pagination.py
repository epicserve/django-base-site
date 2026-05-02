"""
django-ninja paginator preserving the legacy DRF envelope.

The Vue SPA already understands the DRF-shaped response. Every list endpoint
should be decorated with ``@paginate(LegacyPagination)`` (or a subclass that
overrides ``default_page_size``).
"""

import math
from typing import Any
from urllib.parse import urlencode

from django.conf import settings
from django.db.models import QuerySet

from ninja import Schema
from ninja.pagination import PaginationBase


class LegacyPagination(PaginationBase):
    default_page_size: int = 15
    max_page_size: int = 500

    class Input(Schema):
        page: int = 1
        page_size: int | None = None

    class Output(Schema):
        default_ordering: str = ""
        ordering: str = ""
        next: str | None = None
        previous: str | None = None
        count: int
        num_pages: int
        page_size: int
        current_page_num: int
        results: list[Any] = []

    items_attribute: str = "results"

    def paginate_queryset(self, queryset: QuerySet, pagination: Input, **params) -> dict:
        request = params.get("request")
        page = max(pagination.page, 1)
        page_size = pagination.page_size or self.default_page_size
        page_size = max(1, min(page_size, self.max_page_size))

        count = queryset.count() if isinstance(queryset, QuerySet) else len(queryset)
        num_pages = max(1, math.ceil(count / page_size)) if count else 1
        offset = (page - 1) * page_size
        results = list(queryset[offset : offset + page_size])

        ordering = ""
        if request is not None:
            ordering = request.GET.get("ordering", "") or ""
        default_ordering = getattr(self, "default_ordering", "") or ""

        return {
            "default_ordering": default_ordering,
            "ordering": ordering,
            "next": _build_page_url(request, page + 1) if page < num_pages else None,
            "previous": _build_page_url(request, page - 1) if page > 1 else None,
            "count": count,
            "num_pages": num_pages,
            "page_size": page_size,
            "current_page_num": page,
            "results": results,
        }


def _build_page_url(request, page: int) -> str | None:
    if request is None:
        return None
    params = request.GET.copy()
    params["page"] = str(page)
    return f"{request.build_absolute_uri(request.path)}?{urlencode(params, doseq=True)}"


def make_pagination(default_page_size: int = 15, default_ordering: str = "") -> type[LegacyPagination]:
    """Build a ``LegacyPagination`` subclass with view-specific defaults."""
    return type(
        "LegacyPagination_custom",
        (LegacyPagination,),
        {"default_page_size": default_page_size, "default_ordering": default_ordering},
    )


# Convenience instance for the default page size pulled from Django settings.
DEFAULT_PAGE_SIZE = getattr(settings, "DEFAULT_PAGE_SIZE", 15)
LegacyPagination.default_page_size = DEFAULT_PAGE_SIZE
