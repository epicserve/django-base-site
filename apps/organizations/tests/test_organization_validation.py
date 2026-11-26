"""
Field errors from the endpoints that save an organization's own fields.

Creating one used to save whatever it was sent: a blank form made an organization with no name or slug, which broke
every SPA page for its members, and a taken, overlong, or malformed slug answered with a 500.
"""

import json
from unittest.mock import patch

from django.db import IntegrityError

import pytest

from apps.accounts.recipes import make_user
from apps.base.tests import BaseTest
from apps.base.tests.sign_in import sign_in
from apps.organizations.models import Organization, OrganizationMember
from apps.organizations.recipes import make_org

BLANK = "This field cannot be blank."
INVALID_SLUG = "Enter a valid name consisting of letters, numbers, underscores or hyphens."
SLUG_TAKEN = "Account name is already taken."


class TestCreateOrganizationValidation(BaseTest):
    @classmethod
    def setUpTestData(cls):
        cls.kevin = make_user("kevin@example.com")

    def setUp(self):
        sign_in(self.client, self.kevin)

    def _post(self, name, slug):
        return self.client.post(
            "/api/organizations/",
            data=json.dumps({"name": name, "slug": slug}),
            content_type="application/json",
        )

    def _assert_rejected(self, resp, errors):
        assert resp.status_code == 400
        assert resp.json() == errors
        assert not Organization.objects.exists()
        assert not OrganizationMember.objects.exists()

    def test_blank_form(self):
        # What the SPA sends when the form is submitted empty.
        resp = self._post("", "")

        self._assert_rejected(resp, {"name": [BLANK], "slug": [BLANK]})

    def test_blank_name(self):
        resp = self._post("", "acme")

        self._assert_rejected(resp, {"name": [BLANK]})

    def test_name_of_only_spaces(self):
        resp = self._post("   ", "acme")

        self._assert_rejected(resp, {"name": [BLANK]})

    def test_blank_slug(self):
        resp = self._post("Acme", "")

        self._assert_rejected(resp, {"slug": [BLANK]})

    def test_invalid_slug(self):
        resp = self._post("Acme", "acme/inc")

        self._assert_rejected(resp, {"slug": [INVALID_SLUG]})

    def test_slug_too_long(self):
        resp = self._post("Acme", "a" * 41)

        self._assert_rejected(resp, {"slug": ["Ensure this value has at most 40 characters (it has 41)."]})

    def test_duplicate_slug(self):
        existing = make_org(name="Acme", slug="acme")

        resp = self._post("Acme Two", "acme")

        assert resp.status_code == 400
        assert resp.json() == {"slug": [SLUG_TAKEN]}
        assert list(Organization.objects.all()) == [existing]
        assert not OrganizationMember.objects.filter(user=self.kevin).exists()

    def test_non_slug_integrity_error_is_not_reported_as_taken_slug(self):
        def raise_other_integrity_error(self, *args, **kwargs):
            raise IntegrityError("other constraint failed")

        with (
            patch.object(Organization, "save", raise_other_integrity_error),
            pytest.raises(IntegrityError, match="other constraint failed"),
        ):
            self._post("Acme", "acme")

        assert not Organization.objects.exists()
        assert not OrganizationMember.objects.exists()

    def test_strips_surrounding_spaces(self):
        resp = self._post("  Acme  ", " acme ")

        assert resp.status_code == 201
        assert resp.json()["slug"] == "acme"
        assert Organization.objects.filter(name="Acme", slug="acme").exists()

    def test_slug_can_match_a_username(self):
        # Sign-up makes the username from the email address, so acme@example.com is "acme". Organization.clean()
        # refuses a slug that matches any username, which would stop that user naming their organization Acme.
        make_user("acme@example.com", username="acme")

        resp = self._post("Acme", "acme")

        assert resp.status_code == 201
        assert Organization.objects.filter(slug="acme").exists()


class TestUpdateSettingsValidation(BaseTest):
    @classmethod
    def setUpTestData(cls):
        cls.owner = make_user("owner@example.com")
        cls.org = make_org(cls.owner, name="Acme", slug="acme", billing_email="billing@example.com")

    def setUp(self):
        sign_in(self.client, self.owner, self.org)

    def _patch(self, billing_email):
        return self.client.patch(
            "/api/organization-settings/update_settings/",
            data=json.dumps({"billing_email": billing_email}),
            content_type="application/json",
        )

    def test_invalid_billing_email(self):
        resp = self._patch("not-an-email")

        assert resp.status_code == 400
        assert resp.json() == {"billing_email": ["Enter a valid email address."]}
        self.org.refresh_from_db()
        assert self.org.billing_email == "billing@example.com"

    def test_strips_surrounding_spaces(self):
        resp = self._patch("  new@example.com  ")

        assert resp.status_code == 200
        assert resp.json() == {"billing_email": "new@example.com"}
        self.org.refresh_from_db()
        assert self.org.billing_email == "new@example.com"

    def test_checks_only_the_fields_sent(self):
        # A row saved before create validated its slug can still change its billing email.
        Organization.objects.filter(pk=self.org.pk).update(slug="")

        resp = self._patch("new@example.com")

        assert resp.status_code == 200
        self.org.refresh_from_db()
        assert self.org.billing_email == "new@example.com"
