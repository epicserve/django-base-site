from datetime import datetime

from ninja import Schema
from pydantic import ConfigDict

from apps.organizations.roles import OrgPerm, OrgRole


class OrganizationCreateIn(Schema):
    # A name of only spaces would pass the model's blank check.
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str
    slug: str


class OrganizationCreateOut(Schema):
    id: int
    name: str
    slug: str


class SwitchListItemOut(Schema):
    id: int
    name: str
    slug: str
    is_primary: bool
    is_current: bool


class OrgSelectOut(Schema):
    id: int
    slug: str
    name: str
    # The current user's role, and what it lets them do. The SPA checks `permissions`, not `role`.
    role: OrgRole | None
    permissions: list[OrgPerm]


class SuccessOut(Schema):
    success: bool


class SetPrimaryOut(Schema):
    success: bool
    is_primary: bool


class OrgUserOut(Schema):
    id: int
    username: str
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    avatar_url: str | None = None

    @classmethod
    def from_user(cls, u) -> "OrgUserOut":
        return cls(
            id=u.pk,
            username=u.username,
            first_name=u.first_name,
            last_name=u.last_name,
            email=u.email,
            avatar_url=u.avatar_url,
        )


class MemberOut(Schema):
    pk: int
    organization: int
    user: OrgUserOut
    role: OrgRole
    created: datetime
    modified: datetime

    @staticmethod
    def resolve_organization(obj) -> int:
        return obj.organization_id

    @staticmethod
    def resolve_user(obj) -> OrgUserOut:
        return OrgUserOut.from_user(obj.user)


class MemberPatchIn(Schema):
    role: OrgRole | None = None


class InviteOut(Schema):
    pk: int
    organization: int
    sender: int
    invitee: OrgUserOut | None = None
    invitee_email: str = ""
    role: OrgRole
    is_expired: bool
    key: str
    created: datetime
    modified: datetime

    @staticmethod
    def resolve_organization(obj) -> int:
        return obj.organization_id

    @staticmethod
    def resolve_sender(obj) -> int:
        return obj.sender_id

    @staticmethod
    def resolve_invitee(obj) -> OrgUserOut | None:
        # The Members tab shows the invitee's name and avatar, so return the user, not just its id.
        return OrgUserOut.from_user(obj.invitee) if obj.invitee else None


class InviteIn(Schema):
    invitee_email: str
    role: OrgRole = OrgRole.MEMBER


class PublicInviteOut(Schema):
    """Invite payload for unauthenticated lookup at /api/invite-by-key/{key}/."""

    organization_name: str
    sender_name: str
    invitee_email: str = ""
    is_expired: bool
    is_already_member: bool


class SettingsOut(Schema):
    billing_email: str = ""


class SettingsPatchIn(Schema):
    model_config = ConfigDict(str_strip_whitespace=True)

    billing_email: str | None = None
