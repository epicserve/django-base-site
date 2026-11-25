import json

from apps.accounts.tests.recipes import make_user
from apps.base.tests import BaseTest
from apps.base.tests.sign_in import sign_in
from apps.organizations.tests.recipes import make_org
from apps.teams.models import Team
from apps.teams.tests.recipes import make_team

LIST_URL = "/api/teams/"


def _detail_url(pk: int) -> str:
    return f"/api/teams/{pk}/"


class TestTeamAPI(BaseTest):
    @classmethod
    def setUpTestData(cls):
        cls.owner = make_user()
        cls.org = make_org(cls.owner)

    def setUp(self):
        sign_in(self.client, self.owner, self.org)

    def test_list(self):
        team = make_team(self.org, "Engineering")
        make_team(make_org(), "Other Org Team")
        resp = self.client.get(LIST_URL)
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["results"]) == 1
        assert body["results"][0]["id"] == team.pk
        assert body["count"] == 1
        assert body["current_page_num"] == 1

    def test_list_q_search(self):
        make_team(self.org, "Engineering")
        make_team(self.org, "Designers")
        resp = self.client.get(LIST_URL, {"q": "design"})
        names = [r["name"] for r in resp.json()["results"]]
        assert names == ["Designers"]

    def test_create(self):
        resp = self.client.post(
            LIST_URL,
            data=json.dumps({"name": "Engineering", "members": [self.owner.pk]}),
            content_type="application/json",
        )
        assert resp.status_code == 201
        assert Team.objects.count() == 1
        team = Team.objects.get()
        assert team.name == "Engineering"
        assert team.organization == self.org
        assert self.owner in team.members.all()

    def test_create_rejects_someone_outside_the_organization(self):
        # The members picker only offers members, but one can leave before the form is saved.
        outsider = make_user()
        resp = self.client.post(
            LIST_URL,
            data=json.dumps({"name": "Engineering", "members": [self.owner.pk, outsider.pk]}),
            content_type="application/json",
        )
        assert resp.status_code == 400
        assert resp.json() == {"members": [f"User id {outsider.pk} is not a member of this organization."]}
        assert not Team.objects.exists()

    def test_retrieve(self):
        team = make_team(self.org, "Engineering")
        resp = self.client.get(_detail_url(team.pk))
        assert resp.status_code == 200
        assert resp.json()["name"] == "Engineering"

    def test_update(self):
        team = make_team(self.org, "Engineering")
        resp = self.client.patch(
            _detail_url(team.pk),
            data=json.dumps({"name": "Platform"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        team.refresh_from_db()
        assert team.name == "Platform"

    def test_destroy(self):
        team = make_team(self.org, "Engineering")
        resp = self.client.delete(_detail_url(team.pk))
        assert resp.status_code == 204
        assert not Team.objects.filter(pk=team.pk).exists()
