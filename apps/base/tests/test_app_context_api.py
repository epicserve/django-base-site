import json

import pytest
from model_bakery import baker

from apps.accounts.models import User
from apps.base.utils.timezones import get_timezone_label
from apps.organizations.models import OrganizationMember
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


@pytest.mark.django_db
class TestAppContext:
    """`/api/app-context/` goes through `AppContextOut`, which validates and serializes the response."""

    @pytest.fixture(autouse=True)
    def _setup(self, client, settings):
        self.client = client
        settings.SITE_NAME = "Dunder Mifflin"
        settings.INSTANCE = "dev"
        settings.ACCOUNT_SIGNUP_OPEN = True
        self.user = User.objects.create_user(
            username="pam",
            email="pam@example.com",
            password="secret",  # noqa: S106
            first_name="Pam",
            last_name="Beesly",
            timezone="America/New_York",
        )
        self.org = baker.make("organizations.Organization", name="Scranton", slug="scranton")
        OrganizationMember.objects.create(organization=self.org, user=self.user, is_owner=True, is_primary=True)

    def _sign_in(self, org=None):
        # force_login's request has no `user`, so the login signal doesn't select the primary org; set it directly.
        self.client.force_login(self.user)
        if org is not None:
            session = self.client.session
            session["organization_data"] = json.dumps(
                {"pk": org.pk, "id": org.pk, "name": org.name, "slug": org.slug, "is_owner": True}
            )
            session["org_member_count"] = "1"
            session["org_owner_count"] = "1"
            session.save()

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

    def test_signed_in(self, settings):
        settings.DEBUG = True
        self._sign_in(self.org)
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
            "org": {"id": self.org.pk, "name": "Scranton", "slug": "scranton", "is_owner": True},
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
        self._sign_in()

        data = self._get()

        assert data["user"]["organizations"] == []
        assert data["org"] is None
        assert data["organizations"] == []

    def test_billing_enabled(self, settings):
        settings.BILLING_ENABLED = True
        settings.STRIPE_PUBLISHABLE_KEY = "pk_test_123"
        settings.BILLING_FEATURES = [
            {"key": "teams", "label": "Teams", "type": "bool", "default": False},
            {"key": "seats", "label": "Seats", "type": "limit", "default": 3},
        ]
        self._sign_in()

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
