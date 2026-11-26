"""
Build organizations, members and invites.

The tests use these (through `apps.organizations.tests.recipes`), and so does `manage.py seed`, which passes
`update=True` (see `apps.accounts.recipes`).
"""

from datetime import timedelta
from itertools import count

from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.recipes import make_user
from apps.organizations.models import Organization, OrganizationInvite, OrganizationMember
from apps.organizations.roles import OrgRole

_numbers = count(1)


def make_org(
    owner: User | None = None, *, name: str | None = None, slug: str | None = None, update: bool = False, **fields
) -> Organization:
    """
    Make an organization, and when `owner` is given, make them its owner (see `make_member`).

    With `update=True`, an existing organization with that slug gets these values instead.
    """
    number = next(_numbers)
    slug = slug or f"organization-{number}"
    fields["name"] = name or f"Organization {number}"
    if update:
        org, _ = Organization.objects.update_or_create(slug=slug, defaults=fields)
    else:
        org = Organization.objects.create(slug=slug, **fields)
    if owner is not None:
        make_member(org, owner, role=OrgRole.OWNER, update=update)
    return org


def make_member(
    org: Organization,
    user: User | None = None,
    *,
    role: str = OrgRole.MEMBER,
    is_primary: bool | None = None,
    update: bool = False,
) -> User:
    """
    Add `user` (a new `make_user` when None) to `org` with `role`, and return the user.

    The membership is the user's primary one when they don't have one yet, as when they sign up and create their first
    organization, unless `is_primary` says otherwise. With `update=True`, an existing membership gets the role and keeps
    its `is_primary`, which people change in the app.
    """
    user = user or make_user()
    if is_primary is None:
        is_primary = not OrganizationMember.objects.filter(user=user, is_primary=True).exists()
    if update:
        OrganizationMember.objects.update_or_create(
            organization=org,
            user=user,
            defaults={"role": role},
            create_defaults={"role": role, "is_primary": is_primary},
        )
    else:
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
    update: bool = False,
) -> OrganizationInvite:
    """
    Invite `email` (or `invitee`, an existing user) to `org`. `expired=True` backdates it past its expiry.

    With `update=True`, an existing invite to that email gets these values, and a pending one starts its 7 days again.
    """
    if email is None and invitee is None:
        email = f"invitee{next(_numbers)}@example.com"
    fields = {"sender": sender, "invitee": invitee, "role": role}
    if update:
        invite, _ = OrganizationInvite.objects.update_or_create(organization=org, invitee_email=email, defaults=fields)
    else:
        invite = OrganizationInvite(organization=org, invitee_email=email, **fields)
        invite.save()
    if expired or update:
        # `created` is auto_now_add, so backdate (or restart) it with an update that skips save().
        invite.created = timezone.now() - timedelta(days=OrganizationInvite.expired_in_days + 1 if expired else 0)
        OrganizationInvite.objects.filter(pk=invite.pk).update(created=invite.created)
    return invite
