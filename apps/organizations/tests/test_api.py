import json

from django.core import mail
from django.test import override_settings

import pytest
from allauth.account.models import EmailAddress

from apps.accounts.recipes import make_user
from apps.base.tests import BaseTest
from apps.base.tests.mail import record_queued_emails, use_failing_mail_server
from apps.organizations.models import Organization, OrganizationInvite, OrganizationMember
from apps.organizations.recipes import make_invite, make_member, make_org
from apps.organizations.roles import OrgPerm, OrgRole


class OrganizationAPITestBase(BaseTest):
    """Acme, whose owner is signed in with it selected."""

    @classmethod
    def setUpTestData(cls):
        cls.owner = make_user("owner@example.com")
        cls.org = make_org(name="Acme", billing_email="owner@example.com")
        # Not primary, so `test_set_primary` has something to change.
        make_member(cls.org, cls.owner, role=OrgRole.OWNER, is_primary=False)

    def setUp(self):
        self.sign_in(self.owner, self.org)


class TestOrganizationViewSet(OrganizationAPITestBase):
    def test_create(self):
        resp = self.client.post(
            "/api/organizations/",
            data=json.dumps({"name": "New Co", "slug": "new-co"}),
            content_type="application/json",
        )
        assert resp.status_code == 201
        new_org = Organization.objects.get(slug="new-co")
        assert new_org.organizationmember_set.get(user=self.owner).role == OrgRole.OWNER

    def test_switch_list(self):
        other = make_org(name="Other Co")
        make_member(other, self.owner, role=OrgRole.MEMBER)
        resp = self.client.get("/api/organizations/switch-list/")
        assert resp.status_code == 200
        slugs = {o["slug"] for o in resp.json()}
        assert slugs == {self.org.slug, other.slug}

    def test_select(self):
        resp = self.client.post(f"/api/organizations/{self.org.slug}/select/")
        assert resp.status_code == 200
        assert resp.json()["slug"] == self.org.slug
        assert resp.json()["role"] == OrgRole.OWNER
        assert OrgPerm.MANAGE_MEMBERS in resp.json()["permissions"]

    def test_set_primary(self):
        resp = self.client.post(f"/api/organizations/{self.org.slug}/set-primary/")
        assert resp.status_code == 200
        assert resp.json()["is_primary"]
        membership = OrganizationMember.objects.get(organization=self.org, user=self.owner)
        assert membership.is_primary

    def test_signout(self):
        resp = self.client.post("/api/organizations/signout/")
        assert resp.status_code == 200
        assert resp.json()["success"]
        assert "organization_data" not in self.client.session


class TestOrganizationMemberViewSet(OrganizationAPITestBase):
    def test_list(self):
        resp = self.client.get("/api/organization-members/")
        assert resp.status_code == 200
        results = resp.json()["results"]
        assert len(results) == 1
        assert results[0]["user"]["id"] == self.owner.pk

    def test_list_q_search(self):
        make_member(self.org, make_user("alice@example.com", username="alice", first_name="Alice", last_name="Wonder"))
        make_member(self.org, make_user("bob@example.com", username="bob", first_name="Bob", last_name="Builder"))
        resp = self.client.get("/api/organization-members/", {"q": "alice"})
        assert resp.status_code == 200
        results = resp.json()["results"]
        usernames = {r["user"]["username"] for r in results}
        assert "alice" in usernames
        assert "bob" not in usernames

    def test_destroy_member(self):
        new_user = make_member(self.org, make_user("member@example.com"), role=OrgRole.MEMBER)
        membership = OrganizationMember.objects.get(organization=self.org, user=new_user)
        resp = self.client.delete(f"/api/organization-members/{membership.pk}/")
        assert resp.status_code == 204
        assert not OrganizationMember.objects.filter(pk=membership.pk).exists()


# Open, so inviting an address without an account isn't refused (see `TestCreateInviteWhileSignupIsClosed`).
@override_settings(ACCOUNT_SIGNUP_OPEN=True)
class TestOrganizationInviteViewSet(OrganizationAPITestBase):
    def test_list(self):
        invite = make_invite(self.org, self.owner, email="guest@example.com")
        resp = self.client.get("/api/organization-invites/")
        assert resp.status_code == 200
        ids = {r["pk"] for r in resp.json()["results"]}
        assert invite.pk in ids

    def test_create_invite(self):
        with self.captureOnCommitCallbacks(execute=True):
            resp = self.client.post(
                "/api/organization-invites/",
                data=json.dumps({"invitee_email": "guest@example.com", "role": OrgRole.MEMBER}),
                content_type="application/json",
            )
        assert resp.status_code == 201
        assert OrganizationInvite.objects.filter(organization=self.org).count() == 1
        assert len(mail.outbox) == 1
        assert "guest@example.com" in mail.outbox[0].to

    def test_destroy_invite(self):
        invite = make_invite(self.org, self.owner, email="guest@example.com")
        resp = self.client.delete(f"/api/organization-invites/{invite.pk}/")
        assert resp.status_code == 204
        assert not OrganizationInvite.objects.filter(pk=invite.pk).exists()


class TestOrganizationSettingsViewSet(OrganizationAPITestBase):
    def test_retrieve_settings(self):
        resp = self.client.get("/api/organization-settings/")
        assert resp.status_code == 200
        assert resp.json()["billing_email"] == "owner@example.com"

    def test_update_settings(self):
        resp = self.client.patch(
            "/api/organization-settings/update_settings/",
            data=json.dumps({"billing_email": "billing@example.com"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        self.org.refresh_from_db()
        assert self.org.billing_email == "billing@example.com"


class TestInviteList(OrganizationAPITestBase):
    """What the Members tab's invite list needs from the API."""

    def test_list_reports_expired_invites(self):
        pending = make_invite(self.org, self.owner, email="new@example.com")
        expired = make_invite(self.org, self.owner, email="old@example.com", expired=True)

        resp = self.client.get("/api/organization-invites/")

        assert resp.status_code == 200
        is_expired = {invite["pk"]: invite["is_expired"] for invite in resp.json()["results"]}
        assert is_expired == {pending.pk: False, expired.pk: True}

    def test_list_includes_the_invitee(self):
        # The tab shows an invitee's name and avatar; it used to get only the user id and showed a blank name.
        invitee = make_user("jim@example.com", first_name="Jim", last_name="Halpert")
        make_invite(self.org, self.owner, invitee=invitee)
        make_invite(self.org, self.owner, email="new@example.com")

        resp = self.client.get("/api/organization-invites/")

        assert resp.status_code == 200
        invitees = {invite["invitee_email"]: invite["invitee"] for invite in resp.json()["results"]}
        assert invitees == {
            "jim@example.com": {
                "id": invitee.pk,
                "username": invitee.username,
                "first_name": "Jim",
                "last_name": "Halpert",
                "email": "jim@example.com",
                "avatar_url": None,
            },
            "new@example.com": None,
        }


@override_settings(ACCOUNT_SIGNUP_OPEN=True)
class TestCreateInviteEmail(OrganizationAPITestBase):
    @pytest.fixture(autouse=True)
    def _pytest_fixtures(self, monkeypatch, settings):
        self.monkeypatch = monkeypatch
        self.settings_fixture = settings

    def test_a_mail_outage_doesnt_fail_the_invite(self):
        # The invite was saved, then sending its email inline answered with a 500.
        use_failing_mail_server(self.settings_fixture)
        queued = record_queued_emails(self.monkeypatch)

        with self.captureOnCommitCallbacks(execute=True):
            resp = self.client.post(
                "/api/organization-invites/",
                data=json.dumps({"invitee_email": "guest@example.com", "role": OrgRole.MEMBER}),
                content_type="application/json",
            )

        assert resp.status_code == 201
        assert OrganizationInvite.objects.filter(organization=self.org, invitee_email="guest@example.com").exists()
        [message] = queued
        assert message["to"] == ["guest@example.com"]
        assert "/organizations/invite/" in message["body"]


SIGNUP_CLOSED = (
    "Sign-up is closed, so only someone with an account can accept an invite. Turn on sign-up (ACCOUNT_SIGNUP_OPEN) to"
    " invite someone who doesn't have an account."
)


@override_settings(ACCOUNT_SIGNUP_OPEN=False)
class TestCreateInviteWhileSignupIsClosed(OrganizationAPITestBase):
    """Someone without an account can't sign up to accept an invite, so an invite to them is refused."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        make_user("jim@example.com")
        make_user("pam@example.com")
        # On Toby's account, but accepting compares the invite with `User.email` only, so he couldn't accept it either.
        toby = make_user("toby@example.com")
        EmailAddress.objects.create(user=toby, email="toby.flenderson@example.com", verified=True, primary=False)

    def _invite(self, email):
        with self.captureOnCommitCallbacks(execute=True):
            return self.client.post(
                "/api/organization-invites/", data=json.dumps({"invitee_email": email}), content_type="application/json"
            )

    def test_refuses_an_address_without_an_account(self):
        for email in ["guest@example.com", "toby.flenderson@example.com"]:
            with self.subTest(email=email):
                resp = self._invite(email)

                assert resp.status_code == 400
                assert resp.json() == {"invitee_email": [SIGNUP_CLOSED]}
        assert not OrganizationInvite.objects.exists()
        assert mail.outbox == []

    def test_a_malformed_address_gets_the_format_error(self):
        resp = self._invite("not-an-email")

        assert resp.status_code == 400
        assert resp.json() == {"invitee_email": ["Enter a valid email address."]}

    def test_invites_an_existing_account(self):
        # Any case, as accepting compares them.
        for email in ["jim@example.com", "Pam@Example.com"]:
            with self.subTest(email=email):
                resp = self._invite(email)

                assert resp.status_code == 201
        assert sorted(OrganizationInvite.objects.values_list("invitee_email", flat=True)) == [
            "Pam@Example.com",
            "jim@example.com",
        ]
        assert sorted(message.to[0] for message in mail.outbox) == ["Pam@Example.com", "jim@example.com"]

    @override_settings(ACCOUNT_SIGNUP_OPEN=True)
    def test_invites_anyone_while_signup_is_open(self):
        resp = self._invite("guest@example.com")

        assert resp.status_code == 201
        assert OrganizationInvite.objects.filter(invitee_email="guest@example.com").exists()


class TestCreateOrganization(BaseTest):
    """`POST /api/organizations/`: the creator owns the new organization, which is primary only if nothing else is."""

    @classmethod
    def setUpTestData(cls):
        cls.kevin = make_user("kevin@example.com")

    def setUp(self):
        self.sign_in(self.kevin)

    def _create(self, slug):
        resp = self.client.post(
            "/api/organizations/",
            data=json.dumps({"name": slug.title(), "slug": slug}),
            content_type="application/json",
        )
        assert resp.status_code == 201
        return OrganizationMember.objects.get(user=self.kevin, organization__slug=slug)

    def test_first_organization_is_primary(self):
        membership = self._create("first-co")

        assert membership.role == OrgRole.OWNER
        assert membership.is_primary

    def test_keeps_the_existing_primary(self):
        # Sign-in opens the primary organization, so creating another one shouldn't move it, or leave two.
        first = self._create("first-co")
        second = self._create("second-co")

        first.refresh_from_db()
        assert first.is_primary
        assert not second.is_primary
        assert OrganizationMember.objects.filter(user=self.kevin, is_primary=True).count() == 1


class TestDeclineInvite(BaseTest):
    """Declining an invite from its link consumes it, but only for the address it was sent to."""

    @classmethod
    def setUpTestData(cls):
        cls.owner = make_user("michael@example.com")
        cls.org = make_org(cls.owner, name="Dunder Mifflin")
        cls.invitee = make_user("jim@example.com")
        cls.invite = make_invite(cls.org, cls.owner, email="Jim@Example.com")
        cls.other_invite = make_invite(cls.org, cls.owner, email="pam@example.com")

    def _decline(self, invite):
        return self.client.post(f"/api/invite-by-key/{invite.key}/decline/")

    def test_the_invitee_declines(self):
        self.sign_in(self.invitee)

        response = self._decline(self.invite)

        assert (response.status_code, response.json()) == (200, {"success": True})
        assert list(OrganizationInvite.objects.all()) == [self.other_invite]
        assert not OrganizationMember.objects.filter(user=self.invitee).exists()

    def test_someone_else_cannot_decline_it(self):
        self.sign_in(self.invitee)

        response = self._decline(self.other_invite)

        assert response.status_code == 403
        assert OrganizationInvite.objects.count() == 2

    def test_a_signed_out_visitor_cannot_decline_it(self):
        response = self._decline(self.invite)

        assert response.status_code == 401
        assert OrganizationInvite.objects.count() == 2

    def test_an_unknown_key(self):
        self.sign_in(self.invitee)

        assert self._decline(OrganizationInvite(key="abc123notarealkey")).status_code == 404
