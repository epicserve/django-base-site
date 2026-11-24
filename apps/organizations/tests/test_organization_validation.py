"""
Field errors from the endpoints that save an organization's own fields.

Creating one used to save whatever it was sent: a blank form made an organization with no name or slug, which broke
every SPA page for its members, and a taken, overlong, or malformed slug answered with a 500.
"""

import json

from django.db import IntegrityError

import pytest
from model_bakery import baker

from apps.accounts.models import User
from apps.organizations.models import Organization, OrganizationMember

BLANK = "This field cannot be blank."
INVALID_SLUG = "Enter a valid name consisting of letters, numbers, underscores or hyphens."
SLUG_TAKEN = "Account name is already taken."


@pytest.mark.django_db
class TestCreateOrganizationValidation:
    @pytest.fixture()
    def signed_in_client(self, client):
        client.user = baker.make(User, email="kevin@example.com")
        client.force_login(client.user)
        return client

    def _post(self, client, name, slug):
        return client.post(
            "/api/organizations/",
            data=json.dumps({"name": name, "slug": slug}),
            content_type="application/json",
        )

    def _assert_rejected(self, resp, errors):
        assert resp.status_code == 400
        assert resp.json() == errors
        assert not Organization.objects.exists()
        assert not OrganizationMember.objects.exists()

    def test_blank_form(self, signed_in_client):
        # What the SPA sends when the form is submitted empty.
        resp = self._post(signed_in_client, "", "")

        self._assert_rejected(resp, {"name": [BLANK], "slug": [BLANK]})

    def test_blank_name(self, signed_in_client):
        resp = self._post(signed_in_client, "", "acme")

        self._assert_rejected(resp, {"name": [BLANK]})

    def test_name_of_only_spaces(self, signed_in_client):
        resp = self._post(signed_in_client, "   ", "acme")

        self._assert_rejected(resp, {"name": [BLANK]})

    def test_blank_slug(self, signed_in_client):
        resp = self._post(signed_in_client, "Acme", "")

        self._assert_rejected(resp, {"slug": [BLANK]})

    def test_invalid_slug(self, signed_in_client):
        resp = self._post(signed_in_client, "Acme", "acme/inc")

        self._assert_rejected(resp, {"slug": [INVALID_SLUG]})

    def test_slug_too_long(self, signed_in_client):
        resp = self._post(signed_in_client, "Acme", "a" * 41)

        self._assert_rejected(resp, {"slug": ["Ensure this value has at most 40 characters (it has 41)."]})

    def test_duplicate_slug(self, signed_in_client):
        existing = baker.make(Organization, name="Acme", slug="acme")

        resp = self._post(signed_in_client, "Acme Two", "acme")

        assert resp.status_code == 400
        assert resp.json() == {"slug": [SLUG_TAKEN]}
        assert list(Organization.objects.all()) == [existing]
        assert not OrganizationMember.objects.filter(user=signed_in_client.user).exists()

    def test_non_slug_integrity_error_is_not_reported_as_taken_slug(self, signed_in_client, monkeypatch):
        def raise_other_integrity_error(self, *args, **kwargs):
            raise IntegrityError("other constraint failed")

        monkeypatch.setattr(Organization, "save", raise_other_integrity_error)

        with pytest.raises(IntegrityError, match="other constraint failed"):
            self._post(signed_in_client, "Acme", "acme")

        assert not Organization.objects.exists()
        assert not OrganizationMember.objects.exists()

    def test_strips_surrounding_spaces(self, signed_in_client):
        resp = self._post(signed_in_client, "  Acme  ", " acme ")

        assert resp.status_code == 201
        assert resp.json()["slug"] == "acme"
        assert Organization.objects.filter(name="Acme", slug="acme").exists()

    def test_slug_can_match_a_username(self, signed_in_client):
        # Sign-up makes the username from the email address, so acme@example.com is "acme". Organization.clean()
        # refuses a slug that matches any username, which would stop that user naming their organization Acme.
        baker.make(User, username="acme", email="acme@example.com")

        resp = self._post(signed_in_client, "Acme", "acme")

        assert resp.status_code == 201
        assert Organization.objects.filter(slug="acme").exists()


@pytest.mark.django_db
class TestUpdateSettingsValidation:
    @pytest.fixture()
    def owner_client(self, client):
        owner = baker.make(User, email="owner@example.com")
        org = baker.make(Organization, name="Acme", slug="acme", billing_email="billing@example.com")
        baker.make(OrganizationMember, organization=org, user=owner, role="owner")
        client.force_login(owner)
        session = client.session
        session["organization_data"] = json.dumps({"pk": org.pk, "id": org.pk, "name": org.name, "slug": org.slug})
        session.save()
        client.org = org
        return client

    def _patch(self, client, billing_email):
        return client.patch(
            "/api/organization-settings/update_settings/",
            data=json.dumps({"billing_email": billing_email}),
            content_type="application/json",
        )

    def test_invalid_billing_email(self, owner_client):
        resp = self._patch(owner_client, "not-an-email")

        assert resp.status_code == 400
        assert resp.json() == {"billing_email": ["Enter a valid email address."]}
        owner_client.org.refresh_from_db()
        assert owner_client.org.billing_email == "billing@example.com"

    def test_strips_surrounding_spaces(self, owner_client):
        resp = self._patch(owner_client, "  new@example.com  ")

        assert resp.status_code == 200
        assert resp.json() == {"billing_email": "new@example.com"}
        owner_client.org.refresh_from_db()
        assert owner_client.org.billing_email == "new@example.com"

    def test_checks_only_the_fields_sent(self, owner_client):
        # A row saved before create validated its slug can still change its billing email.
        Organization.objects.filter(pk=owner_client.org.pk).update(slug="")

        resp = self._patch(owner_client, "new@example.com")

        assert resp.status_code == 200
        owner_client.org.refresh_from_db()
        assert owner_client.org.billing_email == "new@example.com"
