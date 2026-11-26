from apps.accounts.recipes import make_user
from apps.base.tests import BaseTest
from apps.base.tests.sign_in import api_sign_in, sign_in
from apps.organizations.recipes import make_member, make_org
from apps.organizations.roles import OrgRole

APP_CONTEXT_URL = "/api/app-context/"
SESSION_URL = "/_allauth/browser/v1/auth/session"


class TestSignIn(BaseTest):
    @classmethod
    def setUpTestData(cls):
        cls.pam = make_user("pam@example.com")
        cls.scranton = make_org(cls.pam, name="Scranton", slug="scranton")
        cls.stamford = make_org(name="Stamford", slug="stamford")
        make_member(cls.stamford, cls.pam, role=OrgRole.MEMBER)
        cls.toby = make_user("toby@example.com")

    def _app_context(self):
        response = self.client.get(APP_CONTEXT_URL)
        assert response.status_code == 200
        return response.json()

    def test_selects_the_primary_organization(self):
        sign_in(self.client, self.pam)

        context = self._app_context()
        assert context["user"]["email"] == "pam@example.com"
        assert context["org"]["slug"] == "scranton"
        assert context["org"]["role"] == OrgRole.OWNER

    def test_selects_the_organization_given(self):
        sign_in(self.client, self.pam, self.stamford)

        context = self._app_context()
        assert context["org"]["slug"] == "stamford"
        assert context["org"]["role"] == OrgRole.MEMBER

    def test_selects_none_without_a_membership(self):
        sign_in(self.client, self.toby)

        context = self._app_context()
        assert context["user"]["email"] == "toby@example.com"
        assert context["org"] is None

    def test_records_a_password_sign_in_for_allauth(self):
        # allauth reads this record to decide whether a change, like adding a passkey, needs the password again.
        sign_in(self.client, self.pam)

        response = self.client.get(SESSION_URL)
        assert response.status_code == 200
        assert [method["method"] for method in response.json()["data"]["methods"]] == ["password"]


class TestApiSignIn(BaseTest):
    @classmethod
    def setUpTestData(cls):
        cls.pam = make_user("pam@example.com")

    def test_signs_in_with_the_recipe_password(self):
        response = api_sign_in(self.client, "pam@example.com")

        assert response.status_code == 200
        assert self.client.get(APP_CONTEXT_URL).json()["user"]["email"] == "pam@example.com"
