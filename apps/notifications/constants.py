from django.db import models


class NotificationChannel(models.TextChoices):
    """
    Delivery channels recognized by `notify()`, `send_email()`, and the prefs API.

    Use these constants when declaring `default_channels` in
    `settings.NOTIFICATIONS_CATEGORIES` so the valid set is discoverable and
    typos are caught at import time:

        from apps.notifications.constants import NotificationChannel

        NOTIFICATIONS_CATEGORIES = [
            {
                "key": "comments",
                "label": "Comments",
                "default_channels": (NotificationChannel.IN_APP, NotificationChannel.EMAIL),
            },
        ]
    """

    IN_APP = "in_app", "In-app"
    EMAIL = "email", "Email"
