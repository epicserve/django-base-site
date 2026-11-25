"""End-to-end tests that form labels name their inputs, so screen readers announce them and clicking one focuses it."""

from playwright.sync_api import Page, expect


class TestFormLabels:
    def _expect_every_label_names_an_input(self, page: Page):
        # `control` is null for a label that neither wraps an input nor points at one with `for`.
        unattached = page.locator("label").evaluate_all(
            "labels => labels.filter((label) => !label.control).map((label) => label.textContent.trim())"
        )
        assert unattached == []

    def test_every_form(self, page: Page, live_server, sign_in, user, org, subtests):
        # A superuser, for the test notification form.
        user.is_staff = user.is_superuser = True
        user.save()
        sign_in(user, "/accounts/general/")

        with subtests.test("account general"):
            expect(page.get_by_label("First Name", exact=True)).to_have_value("Michael")
            expect(page.get_by_label("Last Name", exact=True)).to_have_value("Scott")
            expect(page.get_by_label("Timezone", exact=True)).to_have_value("Central Time (US & Canada)")
            # A heading, since it names the photo controls rather than an input.
            expect(page.get_by_role("heading", name="Profile Photo")).to_be_visible()
            self._expect_every_label_names_an_input(page)

        with subtests.test("add email"):
            page.goto(f"{live_server.url}/accounts/email/")
            expect(page.get_by_label("Email", exact=True)).to_have_attribute("placeholder", "New email address")
            self._expect_every_label_names_an_input(page)

        with subtests.test("team form"):
            page.goto(f"{live_server.url}/organizations/{org.slug}/settings/teams/")
            page.get_by_role("button", name="Add Team").click()
            expect(page.get_by_label("Name", exact=True)).to_be_visible()
            expect(page.get_by_label("Members", exact=True)).to_have_attribute("placeholder", "Add members...")
            self._expect_every_label_names_an_input(page)

        with subtests.test("test notification form"):
            page.goto(f"{live_server.url}/test-notifications/")
            expect(page.get_by_label("Recipient", exact=True)).to_be_visible()
            expect(page.get_by_label("Send Email Notification", exact=True)).to_be_checked()
            self._expect_every_label_names_an_input(page)
