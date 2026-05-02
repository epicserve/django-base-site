from collections.abc import Iterable

from django.db.models import Q


class IsActiveQuerySetMixin:
    def filter_active(self, excluded_ids: Iterable | None = None):
        filter_obj = Q(is_active=True)
        if excluded_ids is not None:
            filter_obj |= Q(pk__in=excluded_ids)
        return self.filter(filter_obj)
