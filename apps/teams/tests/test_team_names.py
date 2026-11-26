"""
The teams API checks a team's name, so a bad one gets a field error instead of being saved or causing a 500.

Only the SPA checked that a name wasn't blank, so the API saved a team with no name, and a name already used in the
organization raised an IntegrityError.
"""

import json

from apps.accounts.recipes import make_user
from apps.base.tests import BaseTest
from apps.base.tests.sign_in import sign_in
from apps.organizations.recipes import make_org
from apps.teams.models import Team
from apps.teams.recipes import make_team

BAD_NAMES = {"blank": "", "only spaces": "   ", "too long": "x" * 101, "taken": "Sales"}


class TestTeamNames(BaseTest):
    @classmethod
    def setUpTestData(cls):
        cls.owner = make_user()
        cls.org = make_org(cls.owner, name="Dunder Mifflin", slug="dunder-mifflin")
        cls.sales = make_team(cls.org, "Sales")

    def setUp(self):
        sign_in(self.client, self.owner, self.org)

    def _create(self, name):
        return self.client.post("/api/teams/", data=json.dumps({"name": name}), content_type="application/json")

    def _rename(self, team, name):
        return self.client.patch(
            f"/api/teams/{team.pk}/", data=json.dumps({"name": name}), content_type="application/json"
        )

    def test_create_rejects_a_bad_name(self):
        for label, name in BAD_NAMES.items():
            with self.subTest(label=label):
                response = self._create(name)

                assert response.status_code == 400
                assert list(response.json()) == ["name"]
                assert list(Team.objects.values_list("name", flat=True)) == ["Sales"]

    def test_rename_rejects_a_bad_name(self):
        accounting = make_team(self.org, "Accounting")

        for label, name in BAD_NAMES.items():
            with self.subTest(label=label):
                response = self._rename(accounting, name)

                assert response.status_code == 400
                assert list(response.json()) == ["name"]
                accounting.refresh_from_db()
                assert accounting.name == "Accounting"

    def test_spaces_around_a_name_are_trimmed(self):
        created = self._create("  Warehouse  ")
        renamed = self._rename(self.sales, "  Sales Team  ")

        assert (created.json()["name"], renamed.json()["name"]) == ("Warehouse", "Sales Team")

    def test_renaming_a_team_to_its_own_name_is_fine(self):
        response = self._rename(self.sales, "Sales")

        assert response.status_code == 200

    def test_a_rename_with_a_bad_member_list_saves_nothing(self):
        outsider = make_user()

        response = self.client.patch(
            f"/api/teams/{self.sales.pk}/",
            data=json.dumps({"name": "Warehouse", "members": [outsider.pk]}),
            content_type="application/json",
        )

        assert response.status_code == 400
        self.sales.refresh_from_db()
        assert self.sales.name == "Sales"

    def test_another_organization_can_use_the_name(self):
        make_team(make_org(), "Warehouse")

        response = self._create("Warehouse")

        assert response.status_code == 201
