import json
from datetime import timedelta

from django.contrib.auth import user_logged_in
from django.core import mail
from django.test import TestCase
from django.utils import timezone

import pytest
from model_bakery import baker

from apps.accounts.models import User
from apps.base.tests.mail import record_queued_emails, use_failing_mail_server
from apps.organizations.models import Organization, OrganizationInvite, OrganizationMember
from apps.organizations.roles import OrgPerm, OrgRole
from apps.organizations.signals import user_logged_in_receiver


class OrganizationAPITestBase(TestCase):
    @classmethod
    def setUpClass(cls):
        user_logged_in.disconnect(user_logged_in_receiver)
        super().setUpClass()

    def setUp(self):
        self.user = User.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="secret",  # noqa: S106
        )
        self.org = baker.make("organizations.Organization", name="Acme", billing_email="owner@example.com")
        baker.make("organizations.OrganizationMember", organization=self.org, user=self.user, role=OrgRole.OWNER)

    def _login(self):
        self.client.force_login(self.user)
        session = self.client.session
        session["organization_data"] = json.dumps(
            {"pk": self.org.pk, "id": self.org.pk, "name": self.org.name, "slug": self.org.slug}
        )
        session.save()


class TestOrganizationViewSet(OrganizationAPITestBase):
    def test_create(self):
        self._login()
        resp = self.client.post(
            "/api/organizations/",
            data=json.dumps({"name": "New Co", "slug": "new-co"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201)
        new_org = Organization.objects.get(slug="new-co")
        self.assertEqual(new_org.organizationmember_set.get(user=self.user).role, OrgRole.OWNER)

    def test_switch_list(self):
        other = baker.make("organizations.Organization", name="Other Co")
        baker.make("organizations.OrganizationMember", organization=other, user=self.user, role=OrgRole.MEMBER)
        self._login()
        resp = self.client.get("/api/organizations/switch-list/")
        self.assertEqual(resp.status_code, 200)
        slugs = {o["slug"] for o in resp.json()}
        self.assertEqual(slugs, {self.org.slug, other.slug})

    def test_select(self):
        self._login()
        resp = self.client.post(f"/api/organizations/{self.org.slug}/select/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["slug"], self.org.slug)
        self.assertEqual(resp.json()["role"], OrgRole.OWNER)
        self.assertIn(OrgPerm.MANAGE_MEMBERS, resp.json()["permissions"])

    def test_set_primary(self):
        self._login()
        resp = self.client.post(f"/api/organizations/{self.org.slug}/set-primary/")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["is_primary"])
        membership = OrganizationMember.objects.get(organization=self.org, user=self.user)
        self.assertTrue(membership.is_primary)

    def test_signout(self):
        self._login()
        resp = self.client.post("/api/organizations/signout/")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])
        self.assertNotIn("organization_data", self.client.session)


class TestOrganizationMemberViewSet(OrganizationAPITestBase):
    def test_list(self):
        self._login()
        resp = self.client.get("/api/organization-members/")
        self.assertEqual(resp.status_code, 200)
        results = resp.json()["results"] if isinstance(resp.json(), dict) and "results" in resp.json() else resp.json()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["user"]["id"], self.user.pk)

    def test_list_q_search(self):
        match = User.objects.create_user(
            username="alice",
            first_name="Alice",
            last_name="Wonder",
            email="alice@example.com",
            password="x",  # noqa: S106
        )
        baker.make("organizations.OrganizationMember", organization=self.org, user=match)
        miss = User.objects.create_user(
            username="bob",
            first_name="Bob",
            last_name="Builder",
            email="bob@example.com",
            password="x",  # noqa: S106
        )
        baker.make("organizations.OrganizationMember", organization=self.org, user=miss)
        self._login()
        resp = self.client.get("/api/organization-members/", {"q": "alice"})
        self.assertEqual(resp.status_code, 200)
        results = resp.json()["results"]
        usernames = {r["user"]["username"] for r in results}
        self.assertIn("alice", usernames)
        self.assertNotIn("bob", usernames)

    def test_create_member(self):
        new_user = User.objects.create_user(
            username="member",
            email="member@example.com",
            password="secret",  # noqa: S106
        )
        self._login()
        resp = self.client.post(
            "/api/organization-members/",
            data=json.dumps({"user": new_user.pk, "role": OrgRole.MEMBER}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(OrganizationMember.objects.filter(organization=self.org, user=new_user).exists())

    def test_destroy_member(self):
        new_user = User.objects.create_user(
            username="member",
            email="member@example.com",
            password="secret",  # noqa: S106
        )
        membership = baker.make(
            "organizations.OrganizationMember", organization=self.org, user=new_user, role=OrgRole.MEMBER
        )
        self._login()
        resp = self.client.delete(f"/api/organization-members/{membership.pk}/")
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(OrganizationMember.objects.filter(pk=membership.pk).exists())

    def test_search(self):
        User.objects.create_user(
            username="searchable",
            email="searchable@example.com",
            first_name="Search",
            last_name="Able",
            password="secret",  # noqa: S106
        )
        self._login()
        resp = self.client.get("/api/organization-members/search/", {"q": "Searchable"})
        self.assertEqual(resp.status_code, 200)
        usernames = [u["username"] for u in resp.json()]
        self.assertIn("searchable", usernames)


class TestOrganizationInviteViewSet(OrganizationAPITestBase):
    def test_list(self):
        invite = baker.make(
            "organizations.OrganizationInvite",
            organization=self.org,
            sender=self.user,
            invitee_email="guest@example.com",
        )
        self._login()
        resp = self.client.get("/api/organization-invites/")
        self.assertEqual(resp.status_code, 200)
        results = resp.json()["results"] if isinstance(resp.json(), dict) and "results" in resp.json() else resp.json()
        ids = {r["pk"] for r in results}
        self.assertIn(invite.pk, ids)

    def test_create_invite(self):
        self._login()
        mail.outbox = []
        with self.captureOnCommitCallbacks(execute=True):
            resp = self.client.post(
                "/api/organization-invites/",
                data=json.dumps({"invitee_email": "guest@example.com", "role": OrgRole.MEMBER}),
                content_type="application/json",
            )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(OrganizationInvite.objects.filter(organization=self.org).count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("guest@example.com", mail.outbox[0].to)

    def test_destroy_invite(self):
        invite = baker.make(
            "organizations.OrganizationInvite",
            organization=self.org,
            sender=self.user,
            invitee_email="guest@example.com",
        )
        self._login()
        resp = self.client.delete(f"/api/organization-invites/{invite.pk}/")
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(OrganizationInvite.objects.filter(pk=invite.pk).exists())


class TestOrganizationSettingsViewSet(OrganizationAPITestBase):
    def test_retrieve_settings(self):
        self._login()
        resp = self.client.get("/api/organization-settings/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["billing_email"], "owner@example.com")

    def test_update_settings(self):
        self._login()
        resp = self.client.patch(
            "/api/organization-settings/update_settings/",
            data=json.dumps({"billing_email": "billing@example.com"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.org.refresh_from_db()
        self.assertEqual(self.org.billing_email, "billing@example.com")


@pytest.fixture()
def owner_client(client):
    owner = baker.make(User, email="owner@example.com")
    org = baker.make(Organization, name="Acme")
    baker.make(OrganizationMember, organization=org, user=owner, role=OrgRole.OWNER)
    client.force_login(owner)
    session = client.session
    session["organization_data"] = json.dumps({"pk": org.pk, "id": org.pk, "name": org.name, "slug": org.slug})
    session.save()
    client.org, client.owner = org, owner
    return client


@pytest.mark.django_db
class TestInviteList:
    """What the Members tab's invite list needs from the API."""

    def test_list_reports_expired_invites(self, owner_client):
        org, owner = owner_client.org, owner_client.owner
        pending = OrganizationInvite.objects.create(organization=org, sender=owner, invitee_email="new@example.com")
        expired = OrganizationInvite.objects.create(organization=org, sender=owner, invitee_email="old@example.com")
        OrganizationInvite.objects.filter(pk=expired.pk).update(
            created=timezone.now() - timedelta(days=OrganizationInvite.expired_in_days + 1)
        )

        resp = owner_client.get("/api/organization-invites/")

        assert resp.status_code == 200
        is_expired = {invite["pk"]: invite["is_expired"] for invite in resp.json()["results"]}
        assert is_expired == {pending.pk: False, expired.pk: True}

    def test_list_includes_the_invitee(self, owner_client):
        # The tab shows an invitee's name and avatar; it used to get only the user id and showed a blank name.
        org, owner = owner_client.org, owner_client.owner
        invitee = baker.make(User, email="jim@example.com", first_name="Jim", last_name="Halpert")
        OrganizationInvite.objects.create(organization=org, sender=owner, invitee=invitee)
        OrganizationInvite.objects.create(organization=org, sender=owner, invitee_email="new@example.com")

        resp = owner_client.get("/api/organization-invites/")

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


@pytest.mark.django_db
class TestCreateInviteEmail:
    def test_a_mail_outage_doesnt_fail_the_invite(
        self, owner_client, settings, monkeypatch, django_capture_on_commit_callbacks
    ):
        # The invite was saved, then sending its email inline answered with a 500.
        use_failing_mail_server(settings)
        queued = record_queued_emails(monkeypatch)

        with django_capture_on_commit_callbacks(execute=True):
            resp = owner_client.post(
                "/api/organization-invites/",
                data=json.dumps({"invitee_email": "guest@example.com", "role": OrgRole.MEMBER}),
                content_type="application/json",
            )

        assert resp.status_code == 201
        assert OrganizationInvite.objects.filter(
            organization=owner_client.org, invitee_email="guest@example.com"
        ).exists()
        [message] = queued
        assert message["to"] == ["guest@example.com"]
        assert "/organizations/invite/" in message["body"]


@pytest.mark.django_db
class TestCreateOrganization:
    """`POST /api/organizations/`: the creator owns the new organization, which is primary only if nothing else is."""

    @pytest.fixture()
    def signed_in_client(self, client):
        client.user = baker.make(User, email="kevin@example.com")
        client.force_login(client.user)
        return client

    def _create(self, client, slug):
        resp = client.post(
            "/api/organizations/",
            data=json.dumps({"name": slug.title(), "slug": slug}),
            content_type="application/json",
        )
        assert resp.status_code == 201
        return OrganizationMember.objects.get(user=client.user, organization__slug=slug)

    def test_first_organization_is_primary(self, signed_in_client):
        membership = self._create(signed_in_client, "first-co")

        assert membership.role == OrgRole.OWNER
        assert membership.is_primary

    def test_keeps_the_existing_primary(self, signed_in_client):
        # Sign-in opens the primary organization, so creating another one shouldn't move it, or leave two.
        first = self._create(signed_in_client, "first-co")
        second = self._create(signed_in_client, "second-co")

        first.refresh_from_db()
        assert first.is_primary
        assert not second.is_primary
        assert OrganizationMember.objects.filter(user=signed_in_client.user, is_primary=True).count() == 1
