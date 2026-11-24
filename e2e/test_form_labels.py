"""End-to-end tests that form labels name their inputs, so screen readers announce them and clicking one focuses it."""

import re

import pytest
from playwright.sync_api import Page, expect


class TestFormLabels:
    def _sign_in(self, page: Page, live_server, path: str):
        # Sign-in skips `?next=` for /accounts/* pages, so go to the page afterwards.
        page.goto(f"{live_server.url}/accounts/login/")
        page.get_by_placeholder("Email").fill("michael.scott@dundermifflin.com")
        page.get_by_placeholder("Password").fill("dundermifflin")
        page.get_by_role("button", name="Sign In", exact=True).click()
        page.wait_for_url(re.compile(r"^(?!.*/accounts/login/)"), timeout=10000)
        page.goto(f"{live_server.url}{path}")

    def _expect_every_label_names_an_input(self, page: Page):
        # `control` is null for a label that neither wraps an input nor points at one with `for`.
        unattached = page.locator("label").evaluate_all(
            "labels => labels.filter((label) => !label.control).map((label) => label.textContent.trim())"
        )
        assert unattached == []

    def test_account_general(self, page: Page, live_server, user):
        self._sign_in(page, live_server, "/accounts/general/")
        expect(page.get_by_label("First Name", exact=True)).to_have_value("Michael")
        expect(page.get_by_label("Last Name", exact=True)).to_have_value("Scott")
        expect(page.get_by_label("Timezone", exact=True)).to_have_value("Central Time (US & Canada)")
        # A heading, since it names the photo controls rather than an input.
        expect(page.get_by_role("heading", name="Profile Photo")).to_be_visible()
        self._expect_every_label_names_an_input(page)

    def test_add_email(self, page: Page, live_server, user):
        self._sign_in(page, live_server, "/accounts/email/")
        expect(page.get_by_label("Email", exact=True)).to_have_attribute("placeholder", "New email address")
        self._expect_every_label_names_an_input(page)

    def test_team_form(self, page: Page, live_server, user):
        from apps.organizations.models import Organization, OrganizationMember
        from apps.organizations.roles import OrgRole

        org = Organization.objects.create(name="Dunder Mifflin", slug="dunder-mifflin")
        OrganizationMember.objects.create(organization=org, user=user, role=OrgRole.OWNER, is_primary=True)
        self._sign_in(page, live_server, "/organizations/dunder-mifflin/settings/teams/")
        page.get_by_role("button", name="Add Team").click()
        expect(page.get_by_label("Name", exact=True)).to_be_visible()
        expect(page.get_by_label("Members", exact=True)).to_have_attribute("placeholder", "Add members...")
        self._expect_every_label_names_an_input(page)

    @pytest.fixture()
    def superuser(self, user):
        user.is_staff = user.is_superuser = True
        user.save()
        return user

    def test_test_notification_form(self, page: Page, live_server, superuser):
        self._sign_in(page, live_server, "/test-notifications/")
        expect(page.get_by_label("Recipient", exact=True)).to_be_visible()
        expect(page.get_by_label("Send Email Notification", exact=True)).to_be_checked()
        self._expect_every_label_names_an_input(page)
