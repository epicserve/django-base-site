from datetime import datetime
from typing import Literal

from ninja import Schema


class NotificationActorOut(Schema):
    id: int
    username: str
    full_name: str
    avatar_url: str | None = None


class NotificationOut(Schema):
    id: int
    type: str
    title: str
    body: str
    url: str
    is_read: bool
    created: datetime
    actor: NotificationActorOut | None = None

    @staticmethod
    def resolve_is_read(obj) -> bool:
        return obj.read_at is not None

    @staticmethod
    def resolve_actor(obj) -> NotificationActorOut | None:
        if obj.actor is None:
            return None
        full_name = (obj.actor.get_full_name() or "").strip() or obj.actor.username
        return NotificationActorOut(
            id=obj.actor.pk,
            username=obj.actor.username,
            full_name=full_name,
            avatar_url=obj.actor.avatar_url,
        )


class NotificationPatchIn(Schema):
    is_read: bool | None = None


class UnreadCountOut(Schema):
    count: int


class BulkActionIn(Schema):
    action: Literal["mark_read", "mark_unread", "delete"]
    ids: list[int] | None = None
    all_unread: bool = False


class BulkResultOut(Schema):
    updated: int = 0
    deleted: int = 0
