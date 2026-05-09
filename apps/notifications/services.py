from collections.abc import Sequence
from datetime import datetime
from typing import Any

from django.contrib.contenttypes.models import ContentType
from django.db.models import Model

from apps.accounts.models import User
from apps.notifications.categories import filter_recipients
from apps.notifications.constants import NotificationChannel
from apps.notifications.models import Notification
from apps.organizations.models import Organization, OrganizationMember


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

    When `organization` is set, every recipient must be a member of that org —
    a `ValueError` is raised otherwise. The list-API filters cross-org
    notifications out at read time, but creating misrouted rows would still
    waste storage and skew analytics, so we fail loudly at the producer.
    """
    if organization is not None and recipients:
        member_ids = set(
            OrganizationMember.objects.filter(
                organization=organization,
                user__in=recipients,
            ).values_list("user_id", flat=True)
        )
        outsiders = [r.pk for r in recipients if r.pk not in member_ids]
        if outsiders:
            raise ValueError(
                f"notify(): recipients {outsiders} are not members of "
                f"organization {organization.pk} ({organization.name})."
            )

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
