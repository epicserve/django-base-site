"""
The teams API checks a team's name, so a bad one gets a field error instead of being saved or causing a 500.

Only the SPA checked that a name wasn't blank, so the API saved a team with no name, and a name already used in the
organization raised an IntegrityError.
"""

import json

import pytest
from model_bakery import baker

from apps.accounts.models import User
from apps.organizations.models import Organization, OrganizationMember
from apps.organizations.roles import OrgRole
from apps.teams.models import Team


@pytest.mark.django_db
class TestTeamNames:
    @pytest.fixture(autouse=True)
    def _setup(self, client):
        self.org = baker.make(Organization, name="Dunder Mifflin", slug="dunder-mifflin")
        owner = baker.make(User)
        baker.make(OrganizationMember, organization=self.org, user=owner, role=OrgRole.OWNER)
        self.sales = baker.make(Team, organization=self.org, name="Sales")
        self.client = client
        self.client.force_login(owner)
        session = self.client.session
        session["organization_data"] = json.dumps(
            {"pk": self.org.pk, "id": self.org.pk, "name": self.org.name, "slug": self.org.slug}
        )
        session.save()

    def _create(self, name):
        return self.client.post("/api/teams/", data=json.dumps({"name": name}), content_type="application/json")

    def _rename(self, team, name):
        return self.client.patch(
            f"/api/teams/{team.pk}/", data=json.dumps({"name": name}), content_type="application/json"
        )

    @pytest.mark.parametrize("name", ["", "   ", "x" * 101, "Sales"])
    def test_create_rejects_a_bad_name(self, name):
        response = self._create(name)

        assert response.status_code == 400
        assert list(response.json()) == ["name"]
        assert list(Team.objects.values_list("name", flat=True)) == ["Sales"]

    @pytest.mark.parametrize("name", ["", "   ", "x" * 101, "Sales"])
    def test_rename_rejects_a_bad_name(self, name):
        accounting = baker.make(Team, organization=self.org, name="Accounting")

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
        outsider = baker.make(User)

        response = self.client.patch(
            f"/api/teams/{self.sales.pk}/",
            data=json.dumps({"name": "Warehouse", "members": [outsider.pk]}),
            content_type="application/json",
        )

        assert response.status_code == 400
        self.sales.refresh_from_db()
        assert self.sales.name == "Sales"

    def test_another_organization_can_use_the_name(self):
        baker.make(Team, organization=baker.make(Organization), name="Warehouse")

        response = self._create("Warehouse")

        assert response.status_code == 201
