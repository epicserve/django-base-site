from datetime import datetime

from ninja import Schema
from pydantic import ConfigDict


class MemberDetailOut(Schema):
    id: int
    username: str
    first_name: str = ""
    last_name: str = ""
    avatar_url: str | None = None


class TeamOut(Schema):
    id: int
    name: str
    members: list[int]
    member_details: list[MemberDetailOut]
    created: datetime
    modified: datetime

    @staticmethod
    def resolve_members(obj) -> list[int]:
        return [u.pk for u in obj.members.all()]

    @staticmethod
    def resolve_member_details(obj) -> list[MemberDetailOut]:
        return [
            MemberDetailOut(
                id=u.pk,
                username=u.username,
                first_name=u.first_name,
                last_name=u.last_name,
                avatar_url=u.avatar_url,
            )
            for u in obj.members.all()
        ]


class TeamIn(Schema):
    # A name of only spaces would pass the model's blank check.
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str
    members: list[int] = []


class TeamPatchIn(Schema):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = None
    members: list[int] | None = None
