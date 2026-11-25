"""
The members and invites API tells an organization nothing about users outside it.

Any signed-in user can create an organization and manage its members, so these routes must not. Three used to.
Member search matched any active user's name, username or email and returned their email. Adding a member by user id
put that user in the organization without an invite and returned their email. So did inviting by user id. Counting
through ids got every email.
"""

import json

import pytest
from model_bakery import baker

from apps.accounts.models import User
from apps.organizations.models import Organization, OrganizationInvite, OrganizationMember

OUTSIDER_EMAIL = "jan.levinson@corporate.example"


@pytest.mark.django_db
class TestMembersApiTellsNothingAboutOutsiders:
    @pytest.fixture(autouse=True)
    def _setup(self, client):
        self.outsider = baker.make(
            User, username="jan", first_name="Jan", last_name="Levinson", email=OUTSIDER_EMAIL, is_active=True
        )
        # Nothing special about this user: anyone who signs up can create an organization and own it.
        self.client = client
        self.client.force_login(baker.make(User, email="ryan@example.com"))
        created = self._post("/api/organizations/", {"name": "Ryan Started a Company", "slug": "wuphf"})
        assert created.status_code == 201
        self.org = Organization.objects.get(slug="wuphf")

    def _post(self, url, data):
        return self.client.post(url, data=json.dumps(data), content_type="application/json")

    def _assert_says_nothing_about_the_outsider(self, response):
        body = response.content.decode()
        assert OUTSIDER_EMAIL not in body
        assert "Levinson" not in body

    @pytest.mark.parametrize("query", ["jan", "Levinson", "corporate.example", OUTSIDER_EMAIL])
    def test_search_finds_no_one(self, query):
        response = self.client.get("/api/organization-members/search/", {"q": query})

        assert response.status_code != 200
        self._assert_says_nothing_about_the_outsider(response)

    def test_cant_add_a_user_by_id(self):
        response = self._post("/api/organization-members/", {"user": self.outsider.pk})

        assert response.status_code == 405
        self._assert_says_nothing_about_the_outsider(response)
        assert not OrganizationMember.objects.filter(user=self.outsider).exists()

    def test_cant_invite_a_user_by_id(self):
        response = self._post("/api/organization-invites/", {"invitee": self.outsider.pk})

        assert response.status_code == 400
        self._assert_says_nothing_about_the_outsider(response)
        assert not OrganizationInvite.objects.exists()

    def test_an_email_invite_doesnt_say_whether_the_address_has_an_account(self):
        has_account = self._post("/api/organization-invites/", {"invitee_email": OUTSIDER_EMAIL})
        no_account = self._post("/api/organization-invites/", {"invitee_email": "nobody@corporate.example"})
        invites = self.client.get("/api/organization-invites/")

        assert (has_account.status_code, no_account.status_code) == (201, 201)
        assert has_account.json()["invitee"] is None
        assert no_account.json()["invitee"] is None
        assert "Levinson" not in invites.content.decode()
