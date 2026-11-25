"""End-to-end tests that the two-factor code fields ask a phone for its number pad and for a code it can autofill."""

import re

from playwright.sync_api import Locator, Page, expect


class TestOneTimeCodeFields:
    def _sign_in(self, page: Page, live_server):
        page.goto(f"{live_server.url}/accounts/login/")
        page.get_by_placeholder("Email").fill("michael.scott@dundermifflin.com")
        page.get_by_placeholder("Password").fill("dundermifflin")
        page.get_by_role("button", name="Sign In", exact=True).click()

    def _expect_code_field(self, field: Locator):
        # FormField left attributes that aren't its props on its wrapper <div>, so the input had no `inputmode` and
        # phones showed the full keyboard.
        expect(field).to_have_attribute("inputmode", "numeric")
        expect(field).to_have_attribute("autocomplete", "one-time-code")

    def test_sign_in(self, page: Page, live_server, user):
        from allauth.mfa.totp.internal.auth import TOTP, generate_totp_secret

        TOTP.activate(user, generate_totp_secret())
        self._sign_in(page, live_server)
        page.wait_for_url(re.compile(r"/accounts/2fa/"), timeout=10000)

        # The field takes a recovery code too, which allauth makes of digits only.
        self._expect_code_field(page.get_by_label("Code", exact=True))

    def test_authenticator_app_setup(self, page: Page, sign_in, user):
        sign_in(user, "/accounts/security/totp/")

        self._expect_code_field(page.get_by_label("6-Digit Code"))
