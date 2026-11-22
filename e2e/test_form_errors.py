"""End-to-end tests that field errors belong to their inputs, so screen readers read each error with its input."""

import re

import pytest
from playwright.sync_api import Locator, Page, expect

ANY_VALUE = re.compile(r".*")


class TestFieldErrors:
    def _sign_in(self, page: Page, live_server, path: str):
        # Sign-in skips `?next=` for /accounts/* pages, so go to the page afterwards.
        page.goto(f"{live_server.url}/accounts/login/")
        page.get_by_placeholder("Email").fill("michael.scott@dundermifflin.com")
        page.get_by_placeholder("Password").fill("dundermifflin")
        page.get_by_role("button", name="Sign In", exact=True).click()
        page.wait_for_url(re.compile(r"^(?!.*/accounts/login/)"), timeout=10000)
        page.goto(f"{live_server.url}{path}")

    def _expect_valid(self, field: Locator):
        expect(field).to_be_visible()
        expect(field).not_to_have_attribute("aria-invalid", ANY_VALUE)
        expect(field).not_to_have_attribute("aria-describedby", ANY_VALUE)

    def _expect_error(self, field: Locator, message: str):
        expect(field).to_have_attribute("aria-invalid", "true")
        expect(field).to_have_accessible_description(message)

    @pytest.fixture()
    def org(self, user):
        from apps.organizations.models import Organization, OrganizationMember

        org = Organization.objects.create(name="Dunder Mifflin", slug="dunder-mifflin")
        OrganizationMember.objects.create(organization=org, user=user, is_owner=True, is_primary=True)
        return org

    def test_sign_in(self, page: Page, live_server, user):
        page.goto(f"{live_server.url}/accounts/login/")
        email = page.get_by_placeholder("Email")
        password = page.get_by_placeholder("Password")
        self._expect_valid(password)

        email.fill("michael.scott@dundermifflin.com")
        password.fill("wrong-password")
        page.get_by_role("button", name="Sign In", exact=True).click()

        self._expect_error(password, "The email address and/or password you specified are not correct.")
        self._expect_valid(email)

    def test_add_email(self, page: Page, live_server, user):
        self._sign_in(page, live_server, "/accounts/email/")
        email = page.get_by_label("Email", exact=True)
        self._expect_valid(email)

        email.fill("michael.scott@dundermifflin.com")
        page.get_by_role("button", name="Add", exact=True).click()

        self._expect_error(email, "This email address is already associated with this account.")

    def test_create_organization(self, page: Page, live_server, user):
        # The API doesn't send field errors for this form yet, so the test answers with one.
        page.route(
            re.compile(r".*/api/organizations/$"),
            lambda route: (
                route.fulfill(status=400, json={"slug": ["That account name is taken."]})
                if route.request.method == "POST"
                else route.continue_()
            ),
        )
        self._sign_in(page, live_server, "/organizations/create/")
        name = page.get_by_label("Name", exact=True)
        slug = page.get_by_label("Account Name", exact=True)
        self._expect_valid(slug)

        name.fill("Dunder Mifflin")
        page.get_by_role("button", name="Create").click()

        self._expect_error(slug, "That account name is taken.")
        self._expect_valid(name)

    def test_team_name(self, page: Page, live_server, org):
        self._sign_in(page, live_server, "/organizations/dunder-mifflin/settings/teams/")
        page.get_by_role("button", name="Add Team").click()
        name = page.get_by_label("Name", exact=True)
        self._expect_valid(name)

        page.get_by_role("button", name="Save").click()

        self._expect_error(name, "Name is required.")

    def test_team_members(self, page: Page, live_server, org):
        from apps.accounts.models import User
        from apps.organizations.models import OrganizationMember

        dwight = User.objects.create(email="dwight.schrute@dundermifflin.com", first_name="Dwight", last_name="Schrute")
        membership = OrganizationMember.objects.create(organization=org, user=dwight)
        self._sign_in(page, live_server, "/organizations/dunder-mifflin/settings/teams/")
        page.get_by_role("button", name="Add Team").click()
        page.get_by_label("Name", exact=True).fill("Sales")
        members = page.get_by_label("Members", exact=True)
        self._expect_valid(members)
        members.fill("Dwight")
        page.get_by_role("option", name="Dwight Schrute").click()
        # Gone from the organization by the time the team is saved, so the API rejects him.
        membership.delete()

        page.get_by_role("button", name="Save").click()

        self._expect_error(members, f"User id {dwight.pk} is not a member of this organization.")

    def test_invite_by_email(self, page: Page, live_server, org):
        self._sign_in(page, live_server, "/organizations/dunder-mifflin/settings/members/")
        page.get_by_role("button", name="Invite by Email").click()
        email = page.get_by_label("Email Address", exact=True)
        self._expect_valid(email)

        page.get_by_role("button", name="Send Invite").click()

        self._expect_error(email, "Email is required.")
