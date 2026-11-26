"""End-to-end tests that field errors belong to their inputs, so screen readers read each error with its input."""

import re

from playwright.sync_api import Locator, Page, expect

ANY_VALUE = re.compile(r".*")


class TestFieldErrors:
    def _expect_valid(self, field: Locator):
        expect(field).to_be_visible()
        expect(field).not_to_have_attribute("aria-invalid", ANY_VALUE)
        expect(field).not_to_have_attribute("aria-describedby", ANY_VALUE)

    def _expect_error(self, field: Locator, message: str):
        expect(field).to_have_attribute("aria-invalid", "true")
        expect(field).to_have_accessible_description(message)

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

    def test_every_form(self, page: Page, live_server, sign_in, user, org, subtests):
        # Every submission here is refused, so none of them changes what the next one sees.
        from apps.accounts.recipes import make_user
        from apps.organizations.models import Organization
        from apps.organizations.recipes import make_member

        sign_in(user, "/accounts/email/")

        with subtests.test("add email"):
            email = page.get_by_label("Email", exact=True)
            self._expect_valid(email)

            email.fill(user.email)
            page.get_by_role("button", name="Add", exact=True).click()

            self._expect_error(email, "This email address is already associated with this account.")

        with subtests.test("create a blank organization"):
            # The API used to save it, and every page then threw `Missing required param "slug"`.
            page.goto(f"{live_server.url}/organizations/create/")
            name = page.get_by_label("Name", exact=True)
            slug = page.get_by_label("Account Name", exact=True)
            self._expect_valid(name)
            self._expect_valid(slug)

            page.get_by_role("button", name="Create").click()

            self._expect_error(name, "This field cannot be blank.")
            self._expect_error(slug, "This field cannot be blank.")
            assert list(Organization.objects.all()) == [org]

        with subtests.test("create an organization with a taken account name"):
            # The API used to answer with a 500.
            page.goto(f"{live_server.url}/organizations/create/")
            name = page.get_by_label("Name", exact=True)
            slug = page.get_by_label("Account Name", exact=True)
            self._expect_valid(slug)

            name.fill(org.name)
            expect(slug).to_have_value(org.slug)
            page.get_by_role("button", name="Create").click()

            self._expect_error(slug, "Account name is already taken.")
            self._expect_valid(name)
            assert list(Organization.objects.all()) == [org]

        with subtests.test("team name"):
            page.goto(f"{live_server.url}/organizations/{org.slug}/settings/teams/")
            page.get_by_role("button", name="Add Team").click()
            name = page.get_by_label("Name", exact=True)
            self._expect_valid(name)

            page.get_by_role("button", name="Save").click()

            self._expect_error(name, "Name is required.")

        with subtests.test("team members"):
            dwight = make_member(org, make_user(first_name="Dwight", last_name="Schrute"))
            page.goto(f"{live_server.url}/organizations/{org.slug}/settings/teams/")
            page.get_by_role("button", name="Add Team").click()
            page.get_by_label("Name", exact=True).fill("Sales")
            members = page.get_by_label("Members", exact=True)
            self._expect_valid(members)
            members.fill("Dwight")
            page.get_by_role("option", name="Dwight Schrute").click()
            # Gone from the organization by the time the team is saved, so the API rejects him.
            org.organizationmember_set.filter(user=dwight).delete()

            page.get_by_role("button", name="Save").click()

            self._expect_error(members, f"User id {dwight.pk} is not a member of this organization.")

        with subtests.test("invite by email"):
            page.goto(f"{live_server.url}/organizations/{org.slug}/settings/members/")
            page.get_by_role("button", name="Invite by Email").click()
            email = page.get_by_label("Email Address", exact=True)
            self._expect_valid(email)

            page.get_by_role("button", name="Send Invite").click()

            self._expect_error(email, "Email is required.")
