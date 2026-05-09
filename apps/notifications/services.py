from collections.abc import Sequence
from datetime import datetime
from typing import Any

from django.contrib.contenttypes.models import ContentType
from django.db.models import Model

from apps.accounts.models import User
from apps.notifications.categories import filter_recipients
from apps.notifications.constants import NotificationChannel
from apps.notifications.models import Notification
from apps.organizations.models import Organization


def notify(
    recipients: Sequence[User],
    *,
    title: str,
    url: str | None = None,
    organization: Organization | None = None,
    actor: User | None = None,
    target: Model | None = None,
    body: str = "",
    category: str = "",
    data: dict[str, Any] | None = None,
    expires_at: datetime | None = None,
) -> list[Notification]:
    """
    Create one in-app notification per recipient.

    Producer apps call this; they never touch the model directly. When
    `category` is set and a recipient has the in_app channel disabled for that
    category, that recipient is skipped (the email-side primitive is in
    `apps.base.utils.email.send_email` and gates separately).
    """
    target_ct = None
    target_id = None
    if target is not None:
        target_ct = ContentType.objects.get_for_model(target.__class__)
        target_id = target.pk

    allowed = filter_recipients(recipients, category, NotificationChannel.IN_APP)
    rows = [
        Notification(
            recipient=recipient,
            organization=organization,
            actor=actor,
            target_content_type=target_ct,
            target_object_id=target_id,
            category=category,
            title=title,
            body=body,
            url=url,
            data=data or {},
            expires_at=expires_at,
        )
        for recipient in allowed
    ]
    return Notification.objects.bulk_create(rows)
