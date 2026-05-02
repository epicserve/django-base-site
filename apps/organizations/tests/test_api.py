import json

from django.contrib.auth import user_logged_in
from django.core import mail
from django.test import TestCase

from model_bakery import baker

from apps.accounts.models import User
from apps.organizations.models import Organization, OrganizationInvite, OrganizationMember
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
        baker.make("organizations.OrganizationMember", organization=self.org, user=self.user, is_owner=True)

    def _login(self):
        self.client.force_login(self.user)
        session = self.client.session
        session["organization_data"] = json.dumps(
            {"pk": self.org.pk, "id": self.org.pk, "name": self.org.name, "slug": self.org.slug, "is_owner": True}
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
        self.assertTrue(new_org.is_owner(self.user))

    def test_switch_list(self):
        other = baker.make("organizations.Organization", name="Other Co")
        baker.make("organizations.OrganizationMember", organization=other, user=self.user, is_owner=False)
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
        self.assertTrue(resp.json()["is_owner"])

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
            data=json.dumps({"user": new_user.pk, "is_owner": False}),
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
            "organizations.OrganizationMember", organization=self.org, user=new_user, is_owner=False
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
                data=json.dumps({"invitee_email": "guest@example.com", "is_owner": False}),
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
