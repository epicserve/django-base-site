from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, models, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404

from ninja import Query, Router, Status
from ninja.errors import HttpError
from ninja.pagination import paginate

from apps.base.ninja_pagination import LegacyPagination
from apps.base.permissions import require_authenticated, require_org_perm
from apps.organizations.models import Organization, OrganizationInvite, OrganizationMember
from apps.organizations.roles import OrgPerm, OrgRole, can_assign_role, get_org_role, role_permissions
from apps.organizations.schemas import (
    InviteIn,
    InviteOut,
    MemberOut,
    MemberPatchIn,
    OrganizationCreateIn,
    OrganizationCreateOut,
    OrgSelectOut,
    PublicInviteOut,
    SetPrimaryOut,
    SettingsOut,
    SettingsPatchIn,
    SuccessOut,
    SwitchListItemOut,
)
from apps.organizations.session import remove_org, save_counts, save_org_data

orgs_router = Router(tags=["organizations"])
members_router = Router(tags=["organization-members"])
invites_router = Router(tags=["organization-invites"])
public_invites_router = Router(tags=["public-invites"])
settings_router = Router(tags=["organization-settings"])


# ---------------------------------------------------------------------------
# Organizations
# ---------------------------------------------------------------------------


@orgs_router.post("/", response={201: OrganizationCreateOut})
def create_organization(request, payload: OrganizationCreateIn):
    require_authenticated(request)
    org = Organization(name=payload.name, slug=payload.slug)
    # A blank, overlong, or malformed name or slug becomes a field error. Not full_clean(): Organization.clean()
    # refuses a slug that matches any username, and sign-up gives acme@example.com the username "acme".
    org.clean_fields()
    with transaction.atomic():
        try:
            with transaction.atomic():
                org.save()
        except IntegrityError:
            # The slug's unique index is the check, so a request racing another for the same slug gets this error too.
            # Confirm the slug actually exists so another IntegrityError isn't misattributed to it.
            if Organization.objects.filter(slug=org.slug).exists():
                raise ValidationError({"slug": ["Account name is already taken."]}) from None
            raise
        # Sign-in opens the primary organization, so a new one only becomes primary if the user has none.
        has_primary = OrganizationMember.objects.filter(user=request.user, is_primary=True).exists()
        OrganizationMember.objects.create(
            organization=org, user=request.user, role=OrgRole.OWNER, is_primary=not has_primary
        )
    save_org_data(request, org)
    return Status(201, {"id": org.pk, "name": org.name, "slug": org.slug})


@orgs_router.get("/switch-list/", response=list[SwitchListItemOut])
def switch_list(request):
    require_authenticated(request)
    orgs = Organization.objects.filter(organizationmember__user=request.user).annotate(
        is_primary=models.Subquery(
            OrganizationMember.objects.filter(
                organization=models.OuterRef("pk"),
                user=request.user,
            ).values("is_primary")[:1]
        )
    )
    current_slug = request.org.slug if request.org else None
    return [
        {
            "id": org.pk,
            "name": org.name,
            "slug": org.slug,
            "is_primary": bool(org.is_primary),
            "is_current": org.slug == current_slug,
        }
        for org in orgs
    ]


@orgs_router.post("/signout/", response=SuccessOut)
def signout(request):
    require_authenticated(request)
    remove_org(request)
    return {"success": True}


@orgs_router.post("/{slug}/select/", response=OrgSelectOut)
def select_org(request, slug: str):
    require_authenticated(request)
    org = get_object_or_404(Organization, slug=slug)
    if not org.is_member(request.user):
        raise HttpError(403, "Not a member.")
    save_org_data(request, org)
    role = get_org_role(request.user, org)
    return {"id": org.pk, "slug": org.slug, "name": org.name, "role": role, "permissions": role_permissions(role)}


@orgs_router.post("/{slug}/set-primary/", response=SetPrimaryOut)
def set_primary(request, slug: str):
    require_authenticated(request)
    org = get_object_or_404(Organization, slug=slug)
    with transaction.atomic():
        membership = OrganizationMember.objects.select_for_update().filter(user=request.user, organization=org).first()
        if membership is None:
            raise HttpError(403, "Not a member.")
        if membership.is_primary:
            membership.is_primary = False
            membership.save(update_fields=["is_primary"])
            return {"success": True, "is_primary": False}
        OrganizationMember.objects.filter(user=request.user, is_primary=True).update(is_primary=False)
        membership.is_primary = True
        membership.save(update_fields=["is_primary"])
    return {"success": True, "is_primary": True}


# ---------------------------------------------------------------------------
# Members
# ---------------------------------------------------------------------------


def _require_assignable(request, org, *roles):
    """Raise 403 unless the user may assign every given role (see `can_assign_role`)."""
    if not all(can_assign_role(request.user, org, role) for role in roles):
        raise PermissionDenied("You can't give, change or remove a role with permissions you don't have.")


def _require_permissions_stay_held(org, membership, new_role) -> None:
    """
    Raise 400 if changing the member's role would leave one of its permissions with nobody to hold it.

    Giving a role takes every permission it grants (`can_assign_role`), so a permission nobody holds could never be
    given again. Demoting the last owner would leave nobody who could manage the organization at all. Removing a member
    can't do this: you can't remove yourself, and whoever removes someone holds every permission their role grants.

    Call it in a transaction. It locks the organization's members, so two owners demoting each other at once can't both
    succeed.
    """
    roles = dict(
        OrganizationMember.objects.select_for_update().filter(organization=org).order_by("pk").values_list("pk", "role")
    )
    current_role = roles.pop(membership.pk, membership.role)
    held = {perm for role in [*roles.values(), new_role] for perm in role_permissions(role)}
    lost = [perm for perm in role_permissions(current_role) if perm not in held]
    if lost:
        raise HttpError(
            400,
            f"Nobody else in the organization can {lost[0].label}. Give someone else the {OrgRole(current_role).label}"
            " role first.",
        )


def _members_qs(request):
    return (
        OrganizationMember.objects.select_related("user", "organization")
        .filter_by_org(request)
        .order_by("user__username")
    )


@members_router.get("/", response=list[MemberOut])
@paginate(LegacyPagination)
def list_members(request, q: str | None = Query(None)):
    require_org_perm(request, OrgPerm.MANAGE_MEMBERS)
    qs = _members_qs(request)
    if q:
        qs = qs.filter(
            Q(user__first_name__icontains=q)
            | Q(user__last_name__icontains=q)
            | Q(user__username__icontains=q)
            | Q(user__email__icontains=q)
        )
    return qs


@members_router.get("/{member_id}/", response=MemberOut)
def get_member(request, member_id: int):
    require_org_perm(request, OrgPerm.MANAGE_MEMBERS)
    return get_object_or_404(_members_qs(request), pk=member_id)


@members_router.patch("/{member_id}/", response=MemberOut)
def patch_member(request, member_id: int, payload: MemberPatchIn):
    org = require_org_perm(request, OrgPerm.MANAGE_MEMBERS)
    membership = get_object_or_404(_members_qs(request), pk=member_id)
    if payload.role is not None and payload.role != membership.role:
        _require_assignable(request, org, membership.role, payload.role)
        with transaction.atomic():
            _require_permissions_stay_held(org, membership, payload.role)
            membership.role = payload.role
            membership.save(update_fields=["role", "modified"])
        if membership.role == OrgRole.OWNER:
            membership.send_owner_email(sending_user=request.user)
    return membership


@members_router.delete("/{member_id}/", response={204: None})
def delete_member(request, member_id: int):
    org = require_org_perm(request, OrgPerm.MANAGE_MEMBERS)
    membership = get_object_or_404(_members_qs(request), pk=member_id)
    _require_assignable(request, org, membership.role)
    if membership.user.pk == request.user.pk:
        raise HttpError(400, "You're not allowed to remove yourself from the organization.")
    membership.send_removal_email(sending_user=request.user)
    membership.delete()
    return Status(204, None)


# ---------------------------------------------------------------------------
# Invites
# ---------------------------------------------------------------------------


def _invites_qs(request):
    return (
        OrganizationInvite.objects.select_related("organization", "sender", "invitee")
        .filter_by_org(request)
        .order_by("-created")
    )


@invites_router.get("/", response=list[InviteOut])
@paginate(LegacyPagination)
def list_invites(request):
    require_org_perm(request, OrgPerm.MANAGE_MEMBERS)
    return _invites_qs(request)


@invites_router.post("/", response={201: InviteOut})
def create_invite(request, payload: InviteIn):
    org = require_org_perm(request, OrgPerm.MANAGE_MEMBERS)
    _require_assignable(request, org, payload.role)
    with transaction.atomic():
        invite = OrganizationInvite.objects.create(
            organization=org,
            sender=request.user,
            invitee_email=payload.invitee_email,
            role=payload.role,
        )
        transaction.on_commit(invite.send_invite)
    return Status(201, invite)


@invites_router.get("/{invite_id}/", response=InviteOut)
def get_invite(request, invite_id: int):
    require_org_perm(request, OrgPerm.MANAGE_MEMBERS)
    return get_object_or_404(_invites_qs(request), pk=invite_id)


@invites_router.delete("/{invite_id}/", response={204: None})
def delete_invite(request, invite_id: int):
    org = require_org_perm(request, OrgPerm.MANAGE_MEMBERS)
    invite = get_object_or_404(_invites_qs(request), pk=invite_id)
    _require_assignable(request, org, invite.role)
    with transaction.atomic():
        transaction.on_commit(invite.send_cancellation)
        invite.delete()
    return Status(204, None)


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------


@settings_router.get("/", response=SettingsOut)
def get_settings(request):
    org = require_org_perm(request, OrgPerm.MANAGE_SETTINGS)
    return {"billing_email": org.billing_email or ""}


@settings_router.patch("/update_settings/", response=SettingsOut)
def update_settings(request, payload: SettingsPatchIn):
    org = require_org_perm(request, OrgPerm.MANAGE_SETTINGS)
    data = payload.dict(exclude_unset=True)
    for field, value in data.items():
        setattr(org, field, value)
    # Check only the fields sent, so a slug saved before create checked slugs doesn't block a billing email change.
    org.clean_fields(exclude=[field.name for field in Organization._meta.fields if field.name not in data])
    org.save()
    return {"billing_email": org.billing_email or ""}


# ---------------------------------------------------------------------------
# Public invite lookup (unauthenticated; the email link lands here before sign-in)
# ---------------------------------------------------------------------------


@public_invites_router.get("/{key}/", response=PublicInviteOut, auth=None)
def get_invite_by_key(request, key: str):
    invite = get_object_or_404(OrganizationInvite.objects.select_related("organization", "sender"), key=key)
    is_already_member = bool(request.user.is_authenticated and invite.organization.is_member(request.user))
    return {
        "organization_name": invite.organization.name,
        "sender_name": invite.sender.get_full_name() or invite.sender.email,
        "invitee_email": invite.invitee_email or "",
        "is_expired": invite.is_expired,
        "is_already_member": is_already_member,
    }


@public_invites_router.post("/{key}/accept/", response=SuccessOut)
def accept_invite_by_key(request, key: str):
    require_authenticated(request)
    invite = get_object_or_404(OrganizationInvite.objects.select_related("organization", "sender"), key=key)
    if invite.is_expired:
        raise HttpError(410, "This invite has expired.")
    if invite.invitee_email and invite.invitee_email.lower() != request.user.email.lower():
        raise HttpError(403, "This invitation was sent to a different email address.")
    if invite.organization.is_member(request.user):
        raise HttpError(409, "You're already a member of this organization.")
    # The invite's role holds only while its sender could still assign it, so a sender who has lost permissions since
    # can't hand out roles through invites they sent before.
    role = invite.role if can_assign_role(invite.sender, invite.organization, invite.role) else OrgRole.MEMBER
    with transaction.atomic():
        OrganizationMember.objects.get_or_create(
            organization=invite.organization, user=request.user, defaults={"role": role}
        )
        invite.delete()
    save_counts(request)
    save_org_data(request, invite.organization)
    return {"success": True}


@public_invites_router.post("/{key}/decline/", response=SuccessOut)
def decline_invite_by_key(request, key: str):
    require_authenticated(request)
    invite = get_object_or_404(OrganizationInvite.objects, key=key)
    if invite.invitee_email and invite.invitee_email.lower() != request.user.email.lower():
        raise HttpError(403, "This invitation was sent to a different email address.")
    invite.delete()
    return {"success": True}
