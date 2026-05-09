from dataclasses import asdict

from django.shortcuts import get_object_or_404
from django.utils import timezone

from ninja import Query, Router, Status
from ninja.errors import HttpError
from ninja.pagination import paginate

from apps.base.ninja_pagination import LegacyPagination
from apps.notifications.categories import get_categories, get_category
from apps.notifications.constants import NotificationChannel
from apps.notifications.models import Notification, NotificationPreference
from apps.notifications.schemas import (
    BulkActionIn,
    BulkResultOut,
    NotificationOut,
    NotificationPatchIn,
    NotificationPreferenceOut,
    NotificationPreferencePatchIn,
    UnreadCountOut,
)

router = Router(tags=["notifications"])


def _base_qs(request):
    return Notification.objects.filter_by_org(request).select_related("actor")


@router.get("/", response=list[NotificationOut])
@paginate(LegacyPagination)
def list_notifications(request, is_read: str | None = Query(None)):
    qs = _base_qs(request)
    if is_read is not None:
        want_read = is_read.lower() in ("true", "1", "yes")
        qs = qs.filter(read_at__isnull=not want_read)
    return qs


@router.get("/unread-count/", response=UnreadCountOut)
def unread_count(request):
    return {"count": _base_qs(request).filter(read_at__isnull=True).count()}


def _serialize_category(cat, pref) -> dict:
    return {
        **asdict(cat),
        "in_app": pref.in_app if pref is not None else NotificationChannel.IN_APP in cat.default_channels,
        "email": pref.email if pref is not None else NotificationChannel.EMAIL in cat.default_channels,
    }


@router.get("/preferences/", response=list[NotificationPreferenceOut])
def list_preferences(request):
    """Return one row per registered category, merged with the user's saved preferences."""
    saved = {p.category: p for p in NotificationPreference.objects.filter(user=request.user)}
    return [_serialize_category(cat, saved.get(cat.key)) for cat in get_categories()]


@router.patch("/preferences/{category}/", response=NotificationPreferenceOut)
def patch_preference(request, category: str, payload: NotificationPreferencePatchIn):
    cat = get_category(category)
    if cat is None:
        raise HttpError(404, f"Unknown notification category: {category}")
    pref, _created = NotificationPreference.objects.get_or_create(
        user=request.user,
        category=category,
        defaults={
            "in_app": NotificationChannel.IN_APP in cat.default_channels,
            "email": NotificationChannel.EMAIL in cat.default_channels,
        },
    )
    if payload.in_app is not None:
        pref.in_app = payload.in_app
    if payload.email is not None:
        pref.email = payload.email
    pref.save(update_fields=["in_app", "email", "modified"])
    return _serialize_category(cat, pref)


@router.post("/bulk/", response=BulkResultOut)
def bulk_action(request, payload: BulkActionIn):
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
    return get_object_or_404(_base_qs(request), pk=notification_id)


@router.patch("/{notification_id}/", response=NotificationOut)
def patch_notification(request, notification_id: int, payload: NotificationPatchIn):
    notification = get_object_or_404(_base_qs(request), pk=notification_id)
    if payload.is_read is not None:
        notification.read_at = timezone.now() if payload.is_read else None
        notification.save(update_fields=["read_at", "modified"])
    return notification


@router.delete("/{notification_id}/", response={204: None})
def delete_notification(request, notification_id: int):
    notification = get_object_or_404(_base_qs(request), pk=notification_id)
    notification.delete()
    return Status(204, None)
