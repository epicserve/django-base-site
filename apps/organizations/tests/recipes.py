"""Test data for organizations. Build organizations, members and invites with these instead of by hand."""

from datetime import timedelta
from itertools import count

from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.tests.recipes import make_user
from apps.organizations.models import Organization, OrganizationInvite, OrganizationMember
from apps.organizations.roles import OrgRole

_numbers = count(1)


def make_org(owner: User | None = None, *, name: str | None = None, slug: str | None = None, **fields) -> Organization:
    """Make an organization, and when `owner` is given, make them its owner (see `make_member`)."""
    number = next(_numbers)
    org = Organization.objects.create(
        name=name or f"Organization {number}", slug=slug or f"organization-{number}", **fields
    )
    if owner is not None:
        make_member(org, owner, role=OrgRole.OWNER)
    return org


def make_member(
    org: Organization, user: User | None = None, *, role: str = OrgRole.MEMBER, is_primary: bool | None = None
) -> User:
    """
    Add `user` (a new `make_user` when None) to `org` with `role`, and return the user.

    The membership is the user's primary one when they don't have one yet, as when they sign up and create their first
    organization, unless `is_primary` says otherwise.
    """
    user = user or make_user()
    if is_primary is None:
        is_primary = not OrganizationMember.objects.filter(user=user, is_primary=True).exists()
    OrganizationMember.objects.create(organization=org, user=user, role=role, is_primary=is_primary)
    return user


def make_invite(
    org: Organization,
    sender: User,
    *,
    email: str | None = None,
    invitee: User | None = None,
    role: str = OrgRole.MEMBER,
    expired: bool = False,
) -> OrganizationInvite:
    """Invite `email` (or `invitee`, an existing user) to `org`. `expired=True` backdates it past its expiry."""
    if email is None and invitee is None:
        email = f"invitee{next(_numbers)}@example.com"
    invite = OrganizationInvite(organization=org, sender=sender, invitee=invitee, invitee_email=email, role=role)
    invite.save()
    if expired:
        # `created` is auto_now_add, so backdate it with an update that skips save().
        invite.created = timezone.now() - timedelta(days=OrganizationInvite.expired_in_days + 1)
        OrganizationInvite.objects.filter(pk=invite.pk).update(created=invite.created)
    return invite
