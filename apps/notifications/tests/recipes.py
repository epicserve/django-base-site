"""Test data for notifications."""

from itertools import count

from apps.accounts.models import User
from apps.notifications.constants import NotificationChannel
from apps.notifications.models import Notification

# A category that's on for both channels until the user turns one off. Register it with
# `@override_settings(NOTIFICATIONS_CATEGORIES=[COMMENTS_CATEGORY])`.
COMMENTS_CATEGORY = {
    "key": "comments",
    "label": "Comments",
    "description": "Replies to your posts.",
    "default_channels": (NotificationChannel.IN_APP, NotificationChannel.EMAIL),
}

_numbers = count(1)


def make_notification(recipient: User, **fields) -> Notification:
    """
    Make an unread notification for `recipient`, written straight to the database.

    Unlike `notify()`, it doesn't check `organization` membership or the recipient's preferences, so a test can build a
    row that `notify()` would refuse. Any keyword sets a `Notification` field, such as `organization` or `read_at`.
    """
    fields.setdefault("title", f"Notification {next(_numbers)}")
    return Notification.objects.create(recipient=recipient, **fields)
