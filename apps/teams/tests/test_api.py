import json

from django.contrib.auth import user_logged_in
from django.test import TestCase

from model_bakery import baker

from apps.accounts.models import User
from apps.organizations.signals import user_logged_in_receiver
from apps.teams.models import Team

LIST_URL = "/api/teams/"


def _detail_url(pk: int) -> str:
    return f"/api/teams/{pk}/"


class TestTeamAPI(TestCase):
    @classmethod
    def setUpClass(cls):
        user_logged_in.disconnect(user_logged_in_receiver)
        super().setUpClass()

    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="secret")  # noqa: S106
        self.org = baker.make("organizations.Organization")
        baker.make("organizations.OrganizationMember", organization=self.org, user=self.user, is_owner=True)

    def _login(self):
        self.client.force_login(self.user)
        session = self.client.session
        session["organization_data"] = json.dumps(
            {"pk": self.org.pk, "id": self.org.pk, "name": self.org.name, "slug": self.org.slug, "is_owner": True}
        )
        session.save()

    def test_list(self):
        team = baker.make("teams.Team", name="Engineering", organization=self.org)
        baker.make("teams.Team", name="Other Org Team")
        self._login()
        resp = self.client.get(LIST_URL)
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(len(body["results"]), 1)
        self.assertEqual(body["results"][0]["id"], team.pk)
        self.assertEqual(body["count"], 1)
        self.assertEqual(body["current_page_num"], 1)

    def test_list_q_search(self):
        baker.make("teams.Team", name="Engineering", organization=self.org)
        baker.make("teams.Team", name="Designers", organization=self.org)
        self._login()
        resp = self.client.get(LIST_URL, {"q": "design"})
        names = [r["name"] for r in resp.json()["results"]]
        self.assertEqual(names, ["Designers"])

    def test_create(self):
        self._login()
        resp = self.client.post(
            LIST_URL,
            data=json.dumps({"name": "Engineering", "members": [self.user.pk]}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Team.objects.count(), 1)
        team = Team.objects.get()
        self.assertEqual(team.name, "Engineering")
        self.assertEqual(team.organization, self.org)
        self.assertIn(self.user, team.members.all())

    def test_retrieve(self):
        team = baker.make("teams.Team", name="Engineering", organization=self.org)
        self._login()
        resp = self.client.get(_detail_url(team.pk))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["name"], "Engineering")

    def test_update(self):
        team = baker.make("teams.Team", name="Engineering", organization=self.org)
        self._login()
        resp = self.client.patch(
            _detail_url(team.pk),
            data=json.dumps({"name": "Platform"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        team.refresh_from_db()
        self.assertEqual(team.name, "Platform")

    def test_destroy(self):
        team = baker.make("teams.Team", name="Engineering", organization=self.org)
        self._login()
        resp = self.client.delete(_detail_url(team.pk))
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(Team.objects.filter(pk=team.pk).exists())
