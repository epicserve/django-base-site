import re

from django.apps import apps
from django.conf import settings
from django.db import models, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404

from ninja import Query, Router, Status
from ninja.errors import HttpError
from ninja.pagination import paginate

from apps.base.ninja_pagination import LegacyPagination
from apps.base.permissions import require_authenticated, require_org_owner
from apps.organizations.models import Organization, OrganizationInvite, OrganizationMember
from apps.organizations.schemas import (
    InviteIn,
    InviteOut,
    MemberIn,
    MemberOut,
    MemberPatchIn,
    MemberSearchOut,
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
    with transaction.atomic():
        org = Organization.objects.create(name=payload.name, slug=payload.slug)
        OrganizationMember.objects.create(organization=org, user=request.user, is_owner=True, is_primary=True)
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
    return {"id": org.pk, "slug": org.slug, "name": org.name, "is_owner": org.is_owner(request.user)}


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


def _members_qs(request):
    return (
        OrganizationMember.objects.select_related("user", "organization")
        .filter_by_org(request)
        .order_by("user__username")
    )


@members_router.get("/", response=list[MemberOut])
@paginate(LegacyPagination)
def list_members(request, q: str | None = Query(None)):
    require_org_owner(request)
    qs = _members_qs(request)
    if q:
        qs = qs.filter(
            Q(user__first_name__icontains=q)
            | Q(user__last_name__icontains=q)
            | Q(user__username__icontains=q)
            | Q(user__email__icontains=q)
        )
    return qs


@members_router.get("/search/", response=list[MemberSearchOut])
def search_members(request, q: str = Query("")):
    org = require_org_owner(request)
    user_model = apps.get_model(settings.AUTH_USER_MODEL)
    qs = []
    if len(q) > 2:
        items = [item.strip() for item in re.split(r"\s+", q)]
        q_obj = Q()
        for item in items:
            for fn in ("first_name", "last_name", "username", "email"):
                q_obj |= Q(**{f"{fn}__icontains": item})
        qs = user_model.objects.filter(is_active=True).filter(q_obj)
        qs = qs.exclude(pk__in=OrganizationMember.objects.filter(organization=org).values_list("user_id", flat=True))
        qs = qs.exclude(
            pk__in=OrganizationInvite.objects.filter(organization=org)
            .filter(invitee__isnull=False)
            .values_list("invitee_id", flat=True)
        )
        qs = qs[:10]
    return [
        {
            "pk": u.pk,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "username": u.username,
            "email": u.email,
            "avatar_url": u.avatar_url,
        }
        for u in qs
    ]


@members_router.post("/", response={201: MemberOut})
def create_member(request, payload: MemberIn):
    org = require_org_owner(request)
    membership = OrganizationMember.objects.create(organization=org, user_id=payload.user, is_owner=payload.is_owner)
    return Status(201, membership)


@members_router.get("/{member_id}/", response=MemberOut)
def get_member(request, member_id: int):
    require_org_owner(request)
    return get_object_or_404(_members_qs(request), pk=member_id)


@members_router.patch("/{member_id}/", response=MemberOut)
def patch_member(request, member_id: int, payload: MemberPatchIn):
    require_org_owner(request)
    membership = get_object_or_404(_members_qs(request), pk=member_id)
    was_owner = membership.is_owner
    if payload.is_owner is not None:
        membership.is_owner = payload.is_owner
        membership.save(update_fields=["is_owner", "modified"])
        if not was_owner and membership.is_owner:
            membership.send_owner_email(sending_user=request.user)
    return membership


@members_router.delete("/{member_id}/", response={204: None})
def delete_member(request, member_id: int):
    require_org_owner(request)
    membership = get_object_or_404(_members_qs(request), pk=member_id)
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
    require_org_owner(request)
    return _invites_qs(request)


@invites_router.post("/", response={201: InviteOut})
def create_invite(request, payload: InviteIn):
    org = require_org_owner(request)
    with transaction.atomic():
        invite = OrganizationInvite.objects.create(
            organization=org,
            sender=request.user,
            invitee_email=payload.invitee_email,
            invitee_id=payload.invitee,
            is_owner=payload.is_owner,
        )
        transaction.on_commit(invite.send_invite)
    return Status(201, invite)


@invites_router.get("/{invite_id}/", response=InviteOut)
def get_invite(request, invite_id: int):
    require_org_owner(request)
    return get_object_or_404(_invites_qs(request), pk=invite_id)


@invites_router.delete("/{invite_id}/", response={204: None})
def delete_invite(request, invite_id: int):
    require_org_owner(request)
    invite = get_object_or_404(_invites_qs(request), pk=invite_id)
    with transaction.atomic():
        transaction.on_commit(invite.send_cancellation)
        invite.delete()
    return Status(204, None)


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------


@settings_router.get("/", response=SettingsOut)
def get_settings(request):
    org = require_org_owner(request)
    return {"billing_email": org.billing_email or ""}


@settings_router.patch("/update_settings/", response=SettingsOut)
def update_settings(request, payload: SettingsPatchIn):
    org = require_org_owner(request)
    data = payload.dict(exclude_unset=True)
    for field, value in data.items():
        setattr(org, field, value)
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
    is_owner = invite.is_owner and invite.organization.is_owner(invite.sender)
    with transaction.atomic():
        OrganizationMember.objects.get_or_create(organization=invite.organization, user=request.user, is_owner=is_owner)
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
