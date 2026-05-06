from collections.abc import Sequence
from typing import Any

from django.contrib.contenttypes.models import ContentType
from django.db.models import Model

from apps.accounts.models import User
from apps.notifications.models import Notification
from apps.organizations.models import Organization


def notify(
    recipients: Sequence[User],
    *,
    type: Notification.Type | str,
    title: str,
    url: str,
    organization: Organization | None = None,
    actor: User | None = None,
    target: Model | None = None,
    body: str = "",
    data: dict[str, Any] | None = None,
) -> list[Notification]:
    """Create one notification per recipient. Producer apps call this; they never touch the model directly."""
    if type not in Notification.Type.values:
        raise ValueError(f"Unknown notification type: {type!r}. Valid: {Notification.Type.values}")

    target_ct = None
    target_id = None
    if target is not None:
        target_ct = ContentType.objects.get_for_model(target.__class__)
        target_id = target.pk

    return Notification.objects.bulk_create(
        [
            Notification(
                recipient=recipient,
                organization=organization,
                type=type,
                actor=actor,
                target_content_type=target_ct,
                target_object_id=target_id,
                title=title,
                body=body,
                url=url,
                data=data or {},
            )
            for recipient in recipients
        ]
    )
