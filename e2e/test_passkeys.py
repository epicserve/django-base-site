"""End-to-end tests for adding a passkey on /accounts/security/passkeys/, with Chromium's virtual authenticator."""

import re

import pytest
from allauth.mfa.models import Authenticator
from playwright.sync_api import Page, expect


class TestAddPasskey:
    @pytest.fixture(autouse=True)
    def _virtual_authenticator(self, page: Page):
        # Stands in for a platform authenticator (Touch ID, Windows Hello) for this tab.
        cdp = page.context.new_cdp_session(page)
        cdp.send("WebAuthn.enable")
        cdp.send(
            "WebAuthn.addVirtualAuthenticator",
            {
                "options": {
                    "protocol": "ctap2",
                    "transport": "internal",
                    "hasResidentKey": True,
                    "hasUserVerification": True,
                    "isUserVerified": True,
                }
            },
        )

    def _sign_in(self, page: Page, live_server):
        # Sign-in skips `?next=` for /accounts/* pages, so go to the page afterwards.
        page.goto(f"{live_server.url}/accounts/login/")
        page.get_by_placeholder("Email").fill("michael.scott@dundermifflin.com")
        page.get_by_placeholder("Password").fill("dundermifflin")
        page.get_by_role("button", name="Sign In", exact=True).click()
        page.wait_for_url(re.compile(r"^(?!.*/accounts/login/)"), timeout=10000)
        page.goto(f"{live_server.url}/accounts/security/passkeys/")

    @pytest.mark.parametrize(("passwordless", "kind"), [(True, "Passwordless"), (False, "Two-Factor")])
    def test_add(self, page: Page, live_server, user, passwordless, kind):
        # allauth makes a passkey passwordless when the begin request has a `passwordless` parameter at all, so
        # unchecking the box has to leave it out rather than send `passwordless=false`.
        self._sign_in(page, live_server)

        page.get_by_placeholder("MacBook, YubiKey, iPhone…").fill("Michael's Laptop")
        page.get_by_role("checkbox", name="Allow this passkey to sign me in without a password").set_checked(
            passwordless
        )
        page.get_by_role("button", name="Add Passkey").click()

        expect(page.get_by_text("Michael's Laptop")).to_be_visible()
        expect(page.get_by_text(kind, exact=True)).to_be_visible()
        authenticator = Authenticator.objects.get(user=user, type=Authenticator.Type.WEBAUTHN)
        # `None` for a two-factor passkey: allauth only asks the authenticator about it for a passwordless one.
        assert bool(authenticator.wrap().is_passwordless) is passwordless
