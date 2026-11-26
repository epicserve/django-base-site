from django.test import override_settings

from apps.accounts.recipes import make_user
from apps.base.tests import BaseTest
from apps.base.tests.sign_in import sign_in
from apps.base.utils.timezones import get_timezone_label
from apps.organizations.recipes import make_org
from apps.organizations.roles import OrgPerm, OrgRole
from config.api import api

APP_CONTEXT_URL = "/api/app-context/"

BILLING_DISABLED = {
    "enabled": False,
    "publishable_key": "",
    "plan": None,
    "status": None,
    "billing_cycle": None,
    "trial_end": None,
    "cancel_at_period_end": False,
    "features": {},
}


@override_settings(SITE_NAME="Dunder Mifflin", INSTANCE="dev", ACCOUNT_SIGNUP_OPEN=True)
class TestAppContext(BaseTest):
    """`/api/app-context/` goes through `AppContextOut`, which validates and serializes the response."""

    @classmethod
    def setUpTestData(cls):
        cls.user = make_user(
            "pam@example.com", username="pam", first_name="Pam", last_name="Beesly", timezone="America/New_York"
        )
        cls.org = make_org(cls.user, name="Scranton", slug="scranton")

    def _get(self):
        resp = self.client.get(APP_CONTEXT_URL)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data.pop("version"), str)
        return data

    def test_signed_out(self):
        assert self._get() == {
            "user": None,
            "org": None,
            "organizations": [],
            "orgMemberCount": 0,
            "orgOwnerCount": 0,
            "siteName": "Dunder Mifflin",
            "instance": "dev",
            "debug": False,
            "signupOpen": True,
            "billing": BILLING_DISABLED,
        }

    @override_settings(DEBUG=True)
    def test_signed_in(self):
        sign_in(self.client, self.user, self.org)
        orgs = [{"id": self.org.pk, "name": "Scranton", "slug": "scranton"}]

        assert self._get() == {
            "user": {
                "id": self.user.pk,
                "email": "pam@example.com",
                "username": "pam",
                "first_name": "Pam",
                "last_name": "Beesly",
                "timezone": "America/New_York",
                "timezone_display": get_timezone_label("America/New_York"),
                "avatar_url": None,
                "is_staff": False,
                "is_superuser": False,
                "is_hijacked": False,
                "impersonation_banner_hidden": False,
                "organizations": orgs,
            },
            "org": {
                "id": self.org.pk,
                "name": "Scranton",
                "slug": "scranton",
                "role": OrgRole.OWNER,
                "permissions": list(OrgPerm),
            },
            "organizations": orgs,
            "orgMemberCount": 1,
            "orgOwnerCount": 1,
            "siteName": "Dunder Mifflin",
            "instance": "dev",
            "debug": True,
            "signupOpen": True,
            "billing": BILLING_DISABLED,
        }

    def test_signed_in_without_an_org(self):
        self.org.delete()
        sign_in(self.client, self.user)

        data = self._get()

        assert data["user"]["organizations"] == []
        assert data["org"] is None
        assert data["organizations"] == []

    @override_settings(
        BILLING_ENABLED=True,
        STRIPE_PUBLISHABLE_KEY="pk_test_123",
        BILLING_FEATURES=[
            {"key": "teams", "label": "Teams", "type": "bool", "default": False},
            {"key": "seats", "label": "Seats", "type": "limit", "default": 3},
        ],
    )
    def test_billing_enabled(self):
        for label, user in [
            ("with an organization", self.user),
            ("without an organization", make_user("toby@example.com")),
        ]:
            with self.subTest(label):
                sign_in(self.client, user)

                assert self._get()["billing"] == {
                    **BILLING_DISABLED,
                    "enabled": True,
                    "publishable_key": "pk_test_123",
                    "features": {"teams": False, "seats": 3},
                }


class TestApiResponseSchemas:
    """A route without `response=` generates a TypeScript type with no body, so the SPA has nothing to check."""

    def test_every_route_declares_a_response_body(self):
        missing = [
            f"{method.upper()} {path} -> {status}"
            for path, operations in api.get_openapi_schema()["paths"].items()
            for method, operation in operations.items()
            for status, response in operation["responses"].items()
            if int(status) != 204 and "content" not in response
        ]

        assert missing == []
