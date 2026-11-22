import json

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory

import pytest
from model_bakery import baker

from apps.accounts.models import User
from apps.billing.api import get_subscription
from apps.organizations.models import Organization, OrganizationInvite, OrganizationMember
from apps.organizations.roles import ROLE_PERMISSIONS, OrgPerm, OrgRole, has_org_perm
from apps.organizations.session import MockedOrg


def sign_in(client, user, org):
    client.force_login(user)
    session = client.session
    session["organization_data"] = json.dumps({"pk": org.pk, "id": org.pk, "name": org.name, "slug": org.slug})
    session.save()
    return client


@pytest.fixture()
def org():
    return baker.make(Organization, name="Dunder Mifflin", slug="dunder-mifflin")


@pytest.fixture()
def owner(org):
    user = baker.make(User, email="michael@example.com", first_name="Michael", last_name="Scott")
    baker.make(OrganizationMember, organization=org, user=user, role=OrgRole.OWNER)
    return user


@pytest.fixture()
def member(org):
    user = baker.make(User, email="dwight@example.com", first_name="Dwight", last_name="Schrute")
    baker.make(OrganizationMember, organization=org, user=user, role=OrgRole.MEMBER)
    return user


@pytest.mark.django_db
class TestHasOrgPerm:
    def test_an_owner_has_every_permission(self, org, owner):
        assert all(has_org_perm(owner, org, perm) for perm in OrgPerm)

    def test_a_member_has_none(self, org, member):
        assert not any(has_org_perm(member, org, perm) for perm in OrgPerm)

    def test_someone_outside_the_organization_has_none(self, org):
        outsider = baker.make(User)

        assert not any(has_org_perm(outsider, org, perm) for perm in OrgPerm)

    def test_an_anonymous_user_has_none(self, org):
        assert not any(has_org_perm(AnonymousUser(), org, perm) for perm in OrgPerm)


# One read-only route for each permission. Billing's router is mounted only with BILLING_ENABLED, which test settings
# leave off, so its route is called directly.
ROUTES = {
    OrgPerm.MANAGE_SETTINGS: "/api/organization-settings/",
    OrgPerm.MANAGE_MEMBERS: "/api/organization-members/",
    OrgPerm.MANAGE_TEAMS: "/api/teams/",
}


@pytest.mark.django_db
class TestRoutesCheckTheirPermission:
    """Give the member role one permission at a time: exactly the routes that need it open up."""

    @pytest.mark.parametrize("granted", list(OrgPerm))
    def test_a_role_opens_only_the_routes_its_permissions_cover(self, client, monkeypatch, org, member, granted):
        monkeypatch.setitem(ROLE_PERMISSIONS, OrgRole.MEMBER, frozenset({granted}))
        sign_in(client, member, org)

        statuses = {perm: client.get(url).status_code for perm, url in ROUTES.items()}

        assert statuses == {perm: 200 if perm == granted else 403 for perm in ROUTES}

    @pytest.mark.parametrize("granted", list(OrgPerm))
    def test_billing_needs_manage_billing(self, monkeypatch, org, member, granted):
        monkeypatch.setitem(ROLE_PERMISSIONS, OrgRole.MEMBER, frozenset({granted}))
        request = RequestFactory().get("/api/billing/subscription/")
        request.user = member
        request.org = MockedOrg(pk=org.pk, id=org.pk, name=org.name, slug=org.slug)

        if granted == OrgPerm.MANAGE_BILLING:
            get_subscription(request)
        else:
            with pytest.raises(PermissionDenied):
                get_subscription(request)


@pytest.mark.django_db
class TestCurrentOrgPermissions:
    def test_app_context_lists_the_roles_permissions(self, client, org, member):
        sign_in(client, member, org)

        current = client.get("/api/app-context/").json()["org"]

        assert (current["role"], current["permissions"]) == ("member", [])

    def test_a_role_change_shows_up_without_switching_organizations(self, client, org, owner):
        # The session once cached `is_owner` from when the organization was selected, so a demoted owner kept the
        # owner UI until they switched organizations or signed in again.
        sign_in(client, owner, org)
        assert client.get("/api/app-context/").json()["org"]["role"] == "owner"

        OrganizationMember.objects.filter(organization=org, user=owner).update(role=OrgRole.MEMBER)

        assert client.get("/api/app-context/").json()["org"]["permissions"] == []

    def test_a_session_saved_before_roles_keeps_its_organization(self, client, org, owner):
        client.force_login(owner)
        session = client.session
        session["organization_data"] = json.dumps(
            {"pk": org.pk, "id": org.pk, "name": org.name, "slug": org.slug, "is_owner": True}
        )
        session.save()

        current = client.get("/api/app-context/").json()["org"]

        assert (current["slug"], current["role"]) == ("dunder-mifflin", "owner")


@pytest.mark.django_db
class TestChangeRole:
    def _patch(self, client, membership, role):
        return client.patch(
            f"/api/organization-members/{membership.pk}/",
            data=json.dumps({"role": role}),
            content_type="application/json",
        )

    def test_making_a_member_an_owner_emails_them(self, client, org, owner, member, mailoutbox):
        sign_in(client, owner, org)
        membership = OrganizationMember.objects.get(organization=org, user=member)

        response = self._patch(client, membership, "owner")

        assert (response.status_code, response.json()["role"]) == (200, "owner")
        assert [message.subject for message in mailoutbox] == [
            "You've been made an owner of the Dunder Mifflin organization"
        ]

    def test_making_an_owner_a_member_sends_nothing(self, client, org, owner, mailoutbox):
        other_owner = baker.make(User, email="jan@example.com")
        membership = baker.make(OrganizationMember, organization=org, user=other_owner, role=OrgRole.OWNER)
        sign_in(client, owner, org)

        response = self._patch(client, membership, "member")

        assert (response.status_code, response.json()["role"]) == (200, "member")
        assert mailoutbox == []

    def test_an_unknown_role_is_rejected(self, client, org, owner, member):
        sign_in(client, owner, org)
        membership = OrganizationMember.objects.get(organization=org, user=member)

        response = self._patch(client, membership, "admin")

        # The project's ninja error handler answers validation errors with 400 and field errors.
        assert (response.status_code, list(response.json())) == (400, ["role"])
        membership.refresh_from_db()
        assert membership.role == OrgRole.MEMBER


@pytest.mark.django_db
class TestInviteRole:
    def _accept(self, client, invite):
        return client.post(f"/api/invite-by-key/{invite.key}/accept/")

    def _invite(self, org, sender, role):
        invitee = baker.make(User, email="jim@example.com")
        invite = OrganizationInvite.objects.create(
            organization=org, sender=sender, invitee_email="jim@example.com", role=role
        )
        return invite, invitee

    def test_an_owner_invite_makes_the_invitee_an_owner(self, client, org, owner):
        invite, invitee = self._invite(org, owner, OrgRole.OWNER)
        client.force_login(invitee)

        assert self._accept(client, invite).status_code == 200

        assert OrganizationMember.objects.get(organization=org, user=invitee).role == OrgRole.OWNER

    def test_a_sender_who_lost_manage_members_only_grants_member(self, client, org, owner):
        invite, invitee = self._invite(org, owner, OrgRole.OWNER)
        OrganizationMember.objects.filter(organization=org, user=owner).update(role=OrgRole.MEMBER)
        client.force_login(invitee)

        assert self._accept(client, invite).status_code == 200

        assert OrganizationMember.objects.get(organization=org, user=invitee).role == OrgRole.MEMBER
