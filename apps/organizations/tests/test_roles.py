import json
from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.core import mail

from apps.accounts.recipes import make_user
from apps.base.tests import BaseTest
from apps.organizations.models import OrganizationInvite, OrganizationMember
from apps.organizations.recipes import make_invite, make_member, make_org
from apps.organizations.roles import ROLE_PERMISSIONS, OrgPerm, OrgRole, get_org_role, has_org_perm, role_permissions


def _grant_members(*perms):
    """Give the member role exactly `perms` until the block ends."""
    return patch.dict(ROLE_PERMISSIONS, {OrgRole.MEMBER: frozenset(perms)})


class DunderMifflinTest(BaseTest):
    """Dunder Mifflin, owned by Michael, with Dwight as a member."""

    @classmethod
    def setUpTestData(cls):
        cls.org = make_org(name="Dunder Mifflin", slug="dunder-mifflin")
        cls.owner = make_member(
            cls.org, make_user("michael@example.com", first_name="Michael", last_name="Scott"), role=OrgRole.OWNER
        )
        cls.member = make_member(cls.org, make_user("dwight@example.com", first_name="Dwight", last_name="Schrute"))

    def _membership(self, user):
        return OrganizationMember.objects.get(organization=self.org, user=user)


class TestHasOrgPerm(DunderMifflinTest):
    def test_an_owner_has_every_permission(self):
        assert all(has_org_perm(self.owner, self.org, perm) for perm in OrgPerm)

    def test_a_member_has_none(self):
        assert not any(has_org_perm(self.member, self.org, perm) for perm in OrgPerm)

    def test_someone_outside_the_organization_has_none(self):
        outsider = make_user()

        assert not any(has_org_perm(outsider, self.org, perm) for perm in OrgPerm)

    def test_an_anonymous_user_has_none(self):
        assert not any(has_org_perm(AnonymousUser(), self.org, perm) for perm in OrgPerm)

    def test_an_unrecognized_role_has_none(self):
        OrganizationMember.objects.filter(organization=self.org, user=self.member).update(role="removed_role")

        assert role_permissions("removed_role") == []
        assert role_permissions(None) == []
        assert get_org_role(self.member, self.org) is None
        assert not any(has_org_perm(self.member, self.org, perm) for perm in OrgPerm)


# One read-only route for each permission. Billing's routes are checked in apps/billing/tests/test_roles.py.
ROUTES = {
    OrgPerm.MANAGE_SETTINGS: "/api/organization-settings/",
    OrgPerm.MANAGE_MEMBERS: "/api/organization-members/",
    OrgPerm.MANAGE_TEAMS: "/api/teams/",
}


class TestRoutesCheckTheirPermission(DunderMifflinTest):
    """Give the member role one permission at a time: exactly the routes that need it open up."""

    def test_a_role_opens_only_the_routes_its_permissions_cover(self):
        self.sign_in(self.member, self.org)

        for granted in OrgPerm:
            with self.subTest(granted=granted), _grant_members(granted):
                statuses = {perm: self.client.get(url).status_code for perm, url in ROUTES.items()}

                assert statuses == {perm: 200 if perm == granted else 403 for perm in ROUTES}


class TestCurrentOrgPermissions(DunderMifflinTest):
    def test_app_context_lists_the_roles_permissions(self):
        self.sign_in(self.member, self.org)

        current = self.client.get("/api/app-context/").json()["org"]

        assert (current["role"], current["permissions"]) == (OrgRole.MEMBER, [])

    def test_a_role_change_shows_up_without_switching_organizations(self):
        # The session once cached `is_owner` from when the organization was selected, so a demoted owner kept the
        # owner UI until they switched organizations or signed in again.
        self.sign_in(self.owner, self.org)
        assert self.client.get("/api/app-context/").json()["org"]["role"] == OrgRole.OWNER

        OrganizationMember.objects.filter(organization=self.org, user=self.owner).update(role=OrgRole.MEMBER)

        assert self.client.get("/api/app-context/").json()["org"]["permissions"] == []

    def test_a_session_saved_before_roles_keeps_its_organization(self):
        self.sign_in(self.owner, self.org)
        # Sessions saved before roles also cached `is_owner` with the organization. That key is what this test is about,
        # so the session is edited by hand.
        session = self.client.session
        session["organization_data"] = json.dumps({**json.loads(session["organization_data"]), "is_owner": True})
        session.save()

        current = self.client.get("/api/app-context/").json()["org"]

        assert (current["slug"], current["role"]) == ("dunder-mifflin", OrgRole.OWNER)

    def test_an_unrecognized_role_returns_no_permissions(self):
        OrganizationMember.objects.filter(organization=self.org, user=self.member).update(role="removed_role")
        self.sign_in(self.member, self.org)

        response = self.client.get("/api/app-context/")

        assert response.status_code == 200
        current = response.json()["org"]
        assert (current["role"], current["permissions"]) == (None, [])


class TestChangeRole(DunderMifflinTest):
    def setUp(self):
        self.sign_in(self.owner, self.org)

    def _patch(self, membership, role):
        return self.client.patch(
            f"/api/organization-members/{membership.pk}/",
            data=json.dumps({"role": role}),
            content_type="application/json",
        )

    def test_making_a_member_an_owner_emails_them(self):
        response = self._patch(self._membership(self.member), OrgRole.OWNER)

        assert (response.status_code, response.json()["role"]) == (200, OrgRole.OWNER)
        assert [message.subject for message in mail.outbox] == [
            "You've been made an owner of the Dunder Mifflin organization"
        ]

    def test_making_an_owner_a_member_sends_nothing(self):
        other_owner = make_member(self.org, make_user("jan@example.com"), role=OrgRole.OWNER)

        response = self._patch(self._membership(other_owner), OrgRole.MEMBER)

        assert (response.status_code, response.json()["role"]) == (200, OrgRole.MEMBER)
        assert mail.outbox == []

    def test_an_unknown_role_is_rejected(self):
        membership = self._membership(self.member)

        response = self._patch(membership, "admin")

        # The project's ninja error handler answers validation errors with 400 and field errors.
        assert (response.status_code, list(response.json())) == (400, ["role"])
        membership.refresh_from_db()
        assert membership.role == OrgRole.MEMBER


class TestInviteRole(DunderMifflinTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.invitee = make_user("jim@example.com")
        cls.invite = make_invite(cls.org, cls.owner, email="jim@example.com", role=OrgRole.OWNER)

    def setUp(self):
        self.sign_in(self.invitee)

    def _accept(self):
        return self.client.post(f"/api/invite-by-key/{self.invite.key}/accept/")

    def test_an_owner_invite_makes_the_invitee_an_owner(self):
        assert self._accept().status_code == 200

        assert self._membership(self.invitee).role == OrgRole.OWNER

    def test_a_sender_who_lost_manage_members_only_grants_member(self):
        OrganizationMember.objects.filter(organization=self.org, user=self.owner).update(role=OrgRole.MEMBER)

        assert self._accept().status_code == 200

        assert self._membership(self.invitee).role == OrgRole.MEMBER


class TestRoleGrantsAreBounded(DunderMifflinTest):
    """A role that manages members can't give, change or remove a role with permissions it lacks."""

    @classmethod
    def setUpClass(cls):
        # Stands in for an admin role a project might add: it manages members, and that's all. Dwight has it.
        cls.enterClassContext(_grant_members(OrgPerm.MANAGE_MEMBERS))
        super().setUpClass()

    def _post(self, url, data):
        return self.client.post(url, data=json.dumps(data), content_type="application/json")

    def test_cant_promote_a_member_to_owner(self):
        jim = self._membership(make_member(self.org, role=OrgRole.MEMBER))
        self.sign_in(self.member, self.org)

        response = self.client.patch(
            f"/api/organization-members/{jim.pk}/",
            data=json.dumps({"role": OrgRole.OWNER}),
            content_type="application/json",
        )

        assert response.status_code == 403
        jim.refresh_from_db()
        assert jim.role == OrgRole.MEMBER

    def test_cant_demote_or_remove_an_owner(self):
        membership = self._membership(self.owner)
        self.sign_in(self.member, self.org)

        demote = self.client.patch(
            f"/api/organization-members/{membership.pk}/",
            data=json.dumps({"role": OrgRole.MEMBER}),
            content_type="application/json",
        )
        remove = self.client.delete(f"/api/organization-members/{membership.pk}/")

        assert (demote.status_code, remove.status_code) == (403, 403)
        membership.refresh_from_db()
        assert membership.role == OrgRole.OWNER

    def test_invites_a_member_but_not_an_owner(self):
        self.sign_in(self.member, self.org)

        as_member = self._post("/api/organization-invites/", {"invitee_email": "jim@example.com"})
        as_owner = self._post("/api/organization-invites/", {"invitee_email": "pam@example.com", "role": OrgRole.OWNER})

        assert (as_member.status_code, as_owner.status_code) == (201, 403)
        assert list(OrganizationInvite.objects.values_list("invitee_email", flat=True)) == ["jim@example.com"]

    def test_cancels_a_member_invite_but_not_an_owner_invite(self):
        member_invite = make_invite(self.org, self.owner, email="jim@example.com", role=OrgRole.MEMBER)
        owner_invite = make_invite(self.org, self.owner, email="pam@example.com", role=OrgRole.OWNER)
        self.sign_in(self.member, self.org)

        cancel_member = self.client.delete(f"/api/organization-invites/{member_invite.pk}/")
        cancel_owner = self.client.delete(f"/api/organization-invites/{owner_invite.pk}/")

        assert (cancel_member.status_code, cancel_owner.status_code) == (204, 403)
        assert not OrganizationInvite.objects.filter(pk=member_invite.pk).exists()
        assert OrganizationInvite.objects.filter(pk=owner_invite.pk).exists()

    def test_an_owner_invite_it_sent_grants_member(self):
        invite = make_invite(self.org, self.member, email="jim@example.com", role=OrgRole.OWNER)
        jim = make_user("jim@example.com")
        self.sign_in(jim)

        assert self.client.post(f"/api/invite-by-key/{invite.key}/accept/").status_code == 200

        assert self._membership(jim).role == OrgRole.MEMBER
