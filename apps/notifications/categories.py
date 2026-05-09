"""
Notification categories.

Categories are declared in `settings.NOTIFICATIONS_CATEGORIES`. Each entry is a
plain dict (the cheapest thing to type by hand in `_base.py`):

    from apps.notifications.constants import NotificationChannel

    NOTIFICATIONS_CATEGORIES = [
        {
            "key": "comments",
            "label": "Comments on your posts",
            "description": "When someone replies to a post you authored.",
            "default_channels": (NotificationChannel.IN_APP, NotificationChannel.EMAIL),
        },
    ]

Internally, entries are normalized into `NotificationCategory` dataclasses for
attribute access and type safety. Settings load identically in every Django
process (web, worker, beat, shell), so there is no per-process drift.

Downstream apps add their categories by extending this setting in their own
settings file or via a project-level override — the same pattern as
`INSTALLED_APPS`, `NOTIFICATIONS_TARGET_MODELS`, etc.

The list is what powers the per-user preferences UI and gates delivery through
`should_send` / `filter_recipients`. The starter ships with the list empty.
"""

from collections.abc import Iterable
from dataclasses import dataclass

from django.conf import settings

from apps.notifications.constants import NotificationChannel


@dataclass(frozen=True)
class NotificationCategory:
    key: str
    label: str
    description: str
    default_channels: tuple[str, ...]


DEFAULT_CHANNELS: tuple[str, ...] = (NotificationChannel.IN_APP,)

_CHANNEL_FIELD = {
    NotificationChannel.IN_APP: "in_app",
    NotificationChannel.EMAIL: "email",
}


def _normalize(entry: dict) -> NotificationCategory:
    return NotificationCategory(
        key=entry["key"],
        label=entry.get("label", entry["key"]),
        description=entry.get("description", ""),
        default_channels=tuple(entry.get("default_channels", DEFAULT_CHANNELS)),
    )


def get_category(key: str) -> NotificationCategory | None:
    """Return the category with `key`, or None if not registered."""
    for entry in settings.NOTIFICATIONS_CATEGORIES:
        if entry.get("key") == key:
            return _normalize(entry)
    return None


def get_categories() -> list[NotificationCategory]:
    """Return all categories sorted by label for stable UI rendering."""
    return sorted(
        (_normalize(e) for e in settings.NOTIFICATIONS_CATEGORIES),
        key=lambda c: c.label.lower(),
    )


def filter_recipients(users: Iterable, category: str, channel: str) -> list:
    """
    Return the subset of `users` that should receive `(category, channel)`.

    One query for the whole list — prefer this over per-user `should_send()`
    inside fanouts. Rules (in order):
      - Empty `category` always sends (ad-hoc events).
      - Unregistered `category` always sends (defensive: never silently drop).
      - For each user with no preference row, fall back to the category's
        `default_channels`.
      - For each user with a preference row, honor `in_app` / `email` directly.
    """
    users = list(users)
    if not users or not category:
        return users

    cat = get_category(category)
    if cat is None:
        return users

    default_on = channel in cat.default_channels
    field = _CHANNEL_FIELD.get(channel)

    from apps.notifications.models import NotificationPreference

    prefs_by_user_id = {p.user_id: p for p in NotificationPreference.objects.filter(user__in=users, category=category)}

    out = []
    for u in users:
        pref = prefs_by_user_id.get(u.pk)
        if pref is None:
            if default_on:
                out.append(u)
        elif field is None:
            # Unknown channel — be defensive and allow.
            out.append(u)
        elif getattr(pref, field):
            out.append(u)
    return out


def should_send(user, category: str, channel: str) -> bool:
    """
    Single-user convenience wrapper around `filter_recipients`.

    Prefer `filter_recipients` directly when checking more than one user — it
    runs one query for the whole list instead of N.
    """
    return bool(filter_recipients([user], category, channel))
