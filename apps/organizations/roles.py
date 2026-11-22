"""
Organization roles and the permissions each one grants.

Code checks permissions, never roles: `has_org_perm(user, org, perm)`, or `require_org_perm(request, perm)` in a ninja
route. To add a role, add it to `OrgRole` (with a migration for the field's choices) and give it its permissions in
`ROLE_PERMISSIONS`. To add a permission, add it to `OrgPerm`, grant it in `ROLE_PERMISSIONS`, and check it.
"""

from django.apps import apps
from django.db import models
from django.utils.translation import gettext_lazy as _


class OrgRole(models.TextChoices):
    OWNER = "owner", _("owner")
    MEMBER = "member", _("member")


class OrgPerm(models.TextChoices):
    MANAGE_SETTINGS = "manage_settings", _("manage the organization's settings")
    MANAGE_MEMBERS = "manage_members", _("manage members and invites")
    MANAGE_TEAMS = "manage_teams", _("manage teams")
    MANAGE_BILLING = "manage_billing", _("manage billing")


ROLE_PERMISSIONS: dict[OrgRole, frozenset[OrgPerm]] = {
    OrgRole.OWNER: frozenset(OrgPerm),
    OrgRole.MEMBER: frozenset(),
}


def role_permissions(role: str | None) -> list[OrgPerm]:
    """Return the permissions a role grants, in `OrgPerm`'s order. No role (not a member) grants none."""
    granted = ROLE_PERMISSIONS.get(OrgRole(role), frozenset()) if role else frozenset()
    return [perm for perm in OrgPerm if perm in granted]


def roles_with_perm(perm: OrgPerm) -> list[OrgRole]:
    return [role for role, perms in ROLE_PERMISSIONS.items() if perm in perms]


def get_org_role(user, org) -> OrgRole | None:
    """Return the user's role in the organization, or None if they aren't a member."""
    if org is None or not getattr(user, "is_authenticated", False):
        return None
    member_model = apps.get_model("organizations.OrganizationMember")
    role = member_model.objects.filter(organization=org, user=user).values_list("role", flat=True).first()
    return OrgRole(role) if role else None


def has_org_perm(user, org, perm: OrgPerm) -> bool:
    """Return whether the user's role in the organization grants the permission."""
    return perm in role_permissions(get_org_role(user, org))
