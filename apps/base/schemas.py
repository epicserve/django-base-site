from ninja import Schema

from apps.billing.schemas import BillingSummaryOut
from apps.organizations.schemas import OrgSelectOut


class VersionOut(Schema):
    version: str


class OrgSummaryOut(Schema):
    id: int
    name: str
    slug: str


class AppUserOut(Schema):
    id: int
    email: str
    username: str
    first_name: str
    last_name: str
    timezone: str
    timezone_display: str
    avatar_url: str | None
    is_staff: bool
    is_superuser: bool
    is_hijacked: bool
    impersonation_banner_hidden: bool
    organizations: list[OrgSummaryOut]


class AppContextOut(Schema):
    """Everything the SPA shell needs on load. Keys are camelCase because the SPA's app store reads them as-is."""

    user: AppUserOut | None
    org: OrgSelectOut | None
    organizations: list[OrgSummaryOut]
    orgMemberCount: int
    orgOwnerCount: int
    siteName: str
    instance: str
    debug: bool = False
    signupOpen: bool
    version: str
    billing: BillingSummaryOut


class StaffUserOut(Schema):
    id: int
    full_name: str
    email: str


class MessageOut(Schema):
    message: str
