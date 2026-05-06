from django.shortcuts import get_object_or_404
from django.utils import timezone

from ninja import Query, Router, Status
from ninja.errors import HttpError
from ninja.pagination import paginate

from apps.base.ninja_pagination import LegacyPagination
from apps.base.permissions import require_authenticated
from apps.notifications.models import Notification
from apps.notifications.schemas import (
    BulkActionIn,
    BulkResultOut,
    NotificationOut,
    NotificationPatchIn,
    UnreadCountOut,
)

router = Router(tags=["notifications"])


def _base_qs(request):
    return Notification.objects.filter_by_org(request).select_related("actor")


@router.get("/", response=list[NotificationOut])
@paginate(LegacyPagination)
def list_notifications(request, is_read: str | None = Query(None)):
    require_authenticated(request)
    qs = _base_qs(request)
    if is_read is not None:
        want_read = is_read.lower() in ("true", "1", "yes")
        qs = qs.filter(read_at__isnull=not want_read)
    return qs


@router.get("/unread-count/", response=UnreadCountOut)
def unread_count(request):
    require_authenticated(request)
    return {"count": _base_qs(request).filter(read_at__isnull=True).count()}


@router.post("/bulk/", response=BulkResultOut)
def bulk_action(request, payload: BulkActionIn):
    require_authenticated(request)
    qs = _base_qs(request)
    if payload.all_unread:
        qs = qs.filter(read_at__isnull=True)
    else:
        if not payload.ids:
            raise HttpError(400, "ids must be a non-empty list when all_unread is not set")
        qs = qs.filter(pk__in=payload.ids)

    if payload.action == "delete":
        deleted, _ = qs.delete()
        return {"deleted": deleted}

    now = timezone.now() if payload.action == "mark_read" else None
    updated = qs.update(read_at=now)
    return {"updated": updated}


@router.get("/{notification_id}/", response=NotificationOut)
def get_notification(request, notification_id: int):
    require_authenticated(request)
    return get_object_or_404(_base_qs(request), pk=notification_id)


@router.patch("/{notification_id}/", response=NotificationOut)
def patch_notification(request, notification_id: int, payload: NotificationPatchIn):
    require_authenticated(request)
    notification = get_object_or_404(_base_qs(request), pk=notification_id)
    if payload.is_read is not None:
        notification.read_at = timezone.now() if payload.is_read else None
        notification.save(update_fields=["read_at", "modified"])
    return notification


@router.delete("/{notification_id}/", response={204: None})
def delete_notification(request, notification_id: int):
    require_authenticated(request)
    notification = get_object_or_404(_base_qs(request), pk=notification_id)
    notification.delete()
    return Status(204, None)
