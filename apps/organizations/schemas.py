from datetime import datetime

from ninja import Schema


class OrganizationCreateIn(Schema):
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
    is_owner: bool


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


class MemberOut(Schema):
    pk: int
    organization: int
    user: OrgUserOut
    is_owner: bool
    created: datetime
    modified: datetime

    @staticmethod
    def resolve_organization(obj) -> int:
        return obj.organization_id

    @staticmethod
    def resolve_user(obj) -> OrgUserOut:
        u = obj.user
        return OrgUserOut(
            id=u.pk,
            username=u.username,
            first_name=u.first_name,
            last_name=u.last_name,
            email=u.email,
            avatar_url=u.avatar_url,
        )


class MemberIn(Schema):
    user: int
    is_owner: bool = False


class MemberPatchIn(Schema):
    is_owner: bool | None = None


class MemberSearchOut(Schema):
    pk: int
    first_name: str = ""
    last_name: str = ""
    username: str
    email: str = ""
    avatar_url: str | None = None


class InviteOut(Schema):
    pk: int
    organization: int
    sender: int
    invitee: int | None = None
    invitee_email: str = ""
    is_owner: bool
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
    def resolve_invitee(obj) -> int | None:
        return obj.invitee_id


class InviteIn(Schema):
    invitee_email: str = ""
    invitee: int | None = None
    is_owner: bool = False


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
    billing_email: str | None = None
