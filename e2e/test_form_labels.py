"""End-to-end tests that form labels name their inputs, so screen readers announce them and clicking one focuses it."""

import re

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

    def test_form_field(self, page: Page, live_server, user):
        # FormField, which every account form uses.
        self._sign_in(page, live_server, "/accounts/general/")
        expect(page.get_by_label("First Name", exact=True)).to_have_value("Michael")
        expect(page.get_by_label("Last Name", exact=True)).to_have_value("Scott")

    def test_add_email(self, page: Page, live_server, user):
        self._sign_in(page, live_server, "/accounts/email/")
        expect(page.get_by_label("Email", exact=True)).to_have_attribute("placeholder", "New email address")
