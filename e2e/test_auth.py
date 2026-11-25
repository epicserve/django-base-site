import re

import pytest
from playwright.sync_api import Page, expect

from apps.accounts.tests.totp import current_totp_code

# Holds requestIdleCallback callbacks until the page unloads, the latest a busy browser could run them. It then
# records how many were requested and cancelled, and runs every one, cancelled or not, recording any error. Results
# go to sessionStorage, which outlives the navigation.
DEFERRED_IDLE_CALLBACKS = """
const idleCallbacks = [];
const cancelled = new Set();
window.requestIdleCallback = (callback) => idleCallbacks.push(callback);
window.cancelIdleCallback = (handle) => cancelled.add(handle);
window.addEventListener('pagehide', () => {
  sessionStorage.setItem('idleCallbacksRequested', String(idleCallbacks.length));
  sessionStorage.setItem('idleCallbacksCancelled', String(cancelled.size));
  for (const callback of idleCallbacks) {
    try {
      callback();
    } catch (error) {
      sessionStorage.setItem('idleCallbackError', String(error));
    }
  }
});
"""


@pytest.fixture()
def _login(page: Page, live_server, user):
    """Log in as the test user and wait for redirect to complete."""
    page.goto(f"{live_server.url}/accounts/login/")
    page.get_by_placeholder("Email").fill("michael.scott@dundermifflin.com")
    page.get_by_placeholder("Password").fill("dundermifflin")
    page.get_by_role("button", name="Sign In", exact=True).click()
    page.wait_for_url(f"{live_server.url}/", timeout=10000)


class TestLogin:
    def test_login_page_renders(self, page: Page, live_server):
        page.goto(f"{live_server.url}/accounts/login/")

        expect(page.get_by_placeholder("Email")).to_be_visible()
        expect(page.get_by_placeholder("Password")).to_be_visible()
        expect(page.get_by_role("button", name="Sign In", exact=True)).to_be_visible()

    def test_invalid_credentials_rejected(self, page: Page, live_server, user):
        page.goto(f"{live_server.url}/accounts/login/")

        page.get_by_placeholder("Email").fill("michael.scott@dundermifflin.com")
        page.get_by_placeholder("Password").fill("wrongpassword")
        page.get_by_role("button", name="Sign In", exact=True).click()

        error_pattern = re.compile(r"email address.*not correct|unable to log in", re.IGNORECASE)
        expect(page.get_by_text(error_pattern)).to_be_visible()

    def test_login_with_valid_credentials(self, page: Page, live_server, user):
        page.goto(f"{live_server.url}/accounts/login/")

        page.get_by_placeholder("Email").fill("michael.scott@dundermifflin.com")
        page.get_by_placeholder("Password").fill("dundermifflin")
        page.get_by_role("button", name="Sign In", exact=True).click()

        page.wait_for_url(f"{live_server.url}/", timeout=10000)
        expect(page).not_to_have_url(re.compile(r"/accounts/login"))

    def test_next_cannot_leave_the_site(self, page: Page, live_server, user):
        # Browsers drop the tab from `/<tab>/evil.example`, which leaves `//evil.example`, another site's address.
        page.route(re.compile(r"^https?://evil\.example/"), lambda route: route.fulfill(body="Another site"))
        page.goto(f"{live_server.url}/accounts/login/?next=/%09/evil.example/")

        page.get_by_placeholder("Email").fill("michael.scott@dundermifflin.com")
        page.get_by_placeholder("Password").fill("dundermifflin")
        page.get_by_role("button", name="Sign In", exact=True).click()

        page.wait_for_url(f"{live_server.url}/", timeout=10000)


class TestLogout:
    @pytest.mark.usefixtures("_login")
    def test_logout_redirects_to_login(self, page: Page, live_server):
        page.goto(f"{live_server.url}/accounts/logout/")

        page.wait_for_url(re.compile(r"/accounts/login"), timeout=10000)
        expect(page.get_by_placeholder("Email")).to_be_visible()
        expect(page.get_by_role("button", name="Sign In", exact=True)).to_be_visible()

    @pytest.mark.usefixtures("_login")
    def test_logout_cancels_the_timezone_check(self, page: Page, live_server):
        # The timezone check waits for an idle moment. It used to stay scheduled after logging out, then throw because
        # the user was gone. The stub runs it at unload even though it's cancelled, so the check's own guard is covered.
        page.add_init_script(DEFERRED_IDLE_CALLBACKS)

        page.goto(f"{live_server.url}/accounts/logout/")
        page.wait_for_url(re.compile(r"/accounts/login"), timeout=10000)

        stored = page.evaluate("Object.fromEntries(Object.entries(sessionStorage))")
        assert int(stored["idleCallbacksRequested"]) > 0
        assert stored["idleCallbacksCancelled"] == stored["idleCallbacksRequested"]
        assert "idleCallbackError" not in stored


class TestAuthRedirects:
    def test_unauthenticated_user_redirected_to_login(self, page: Page, live_server):
        page.goto(f"{live_server.url}/accounts/general/")

        expect(page).to_have_url(re.compile(r"/accounts/login"))
        expect(page.get_by_placeholder("Email")).to_be_visible()


def watch_app_context_requests(page: Page) -> list[str]:
    """Collect the URL of each /api/app-context/ request the page makes from now on."""
    urls: list[str] = []
    page.on("request", lambda request: "/api/app-context/" in request.url and urls.append(request.url))
    return urls


class TestSignInLoadsTheAppContextOnce:
    """
    Signing in ends with a full page load, which fetches /api/app-context/ for the new session.

    The sign-in pages used to fetch it once more just before leaving, and the page load threw that away.
    """

    def test_password(self, page: Page, live_server, user):
        page.goto(f"{live_server.url}/accounts/login/")
        # The page renders once its own app context has loaded.
        expect(page.get_by_role("button", name="Sign In", exact=True)).to_be_visible()
        requests = watch_app_context_requests(page)

        page.get_by_placeholder("Email").fill("michael.scott@dundermifflin.com")
        page.get_by_placeholder("Password").fill("dundermifflin")
        page.get_by_role("button", name="Sign In", exact=True).click()

        page.wait_for_url(f"{live_server.url}/", timeout=10000)
        expect(page.get_by_role("button", name=re.compile(r"^Notifications"))).to_be_visible()
        assert len(requests) == 1

    def test_two_factor(self, page: Page, live_server, user):
        from allauth.mfa.totp.internal.auth import TOTP, generate_totp_secret

        secret = generate_totp_secret()
        TOTP.activate(user, secret)
        page.goto(f"{live_server.url}/accounts/login/")
        page.get_by_placeholder("Email").fill("michael.scott@dundermifflin.com")
        page.get_by_placeholder("Password").fill("dundermifflin")
        page.get_by_role("button", name="Sign In", exact=True).click()
        page.wait_for_url(re.compile(r"/accounts/2fa/"), timeout=10000)
        requests = watch_app_context_requests(page)

        page.get_by_label("Code", exact=True).fill(current_totp_code(secret))
        page.get_by_role("button", name="Continue").click()

        page.wait_for_url(f"{live_server.url}/", timeout=10000)
        expect(page.get_by_role("button", name=re.compile(r"^Notifications"))).to_be_visible()
        assert len(requests) == 1


# Stands in for the browser's WebAuthn API: records each navigator.credentials.get() call and leaves it
# pending (like a passkey prompt nobody answers) until its AbortSignal fires.
FAKE_WEBAUTHN = """
window.__credentialRequests = [];
PublicKeyCredential.isConditionalMediationAvailable = async () => true;
navigator.credentials.get = (options = {}) =>
  new Promise((resolve, reject) => {
    const request = { mediation: options.mediation ?? null, aborted: false };
    window.__credentialRequests.push(request);
    options.signal?.addEventListener('abort', () => {
      request.aborted = true;
      reject(new DOMException('Aborted', 'AbortError'));
    });
  });
"""


class TestPasskeyPrompt:
    """
    The login page offers passkeys through autofill instead of the browser's modal passkey dialog.

    It used to call navigator.credentials.get() with no mediation on load. In Chrome that opens a dialog
    that blocks the page, so the password form couldn't be used until the dialog was dismissed.
    """

    @pytest.fixture(autouse=True)
    def _fake_webauthn(self, page: Page):
        page.add_init_script(FAKE_WEBAUTHN)

    @staticmethod
    def _requests(page: Page, count: int):
        # A function, not an expression: Playwright runs an expression through eval(), which the CSP blocks.
        page.wait_for_function("count => window.__credentialRequests.length === count", arg=count)
        return page.evaluate("window.__credentialRequests")

    def test_offers_passkeys_through_autofill(self, page: Page, live_server):
        page.goto(f"{live_server.url}/accounts/login/")

        assert self._requests(page, 1) == [{"mediation": "conditional", "aborted": False}]
        expect(page.get_by_placeholder("Email")).to_have_attribute("autocomplete", "username webauthn")

    def test_passkey_button_replaces_the_autofill_request(self, page: Page, live_server):
        page.goto(f"{live_server.url}/accounts/login/")
        self._requests(page, 1)

        page.get_by_role("button", name="Sign In with a Passkey").click()

        assert self._requests(page, 2) == [
            {"mediation": "conditional", "aborted": True},
            {"mediation": None, "aborted": False},
        ]

    def test_password_sign_in_works_while_autofill_waits(self, page: Page, live_server, user):
        page.goto(f"{live_server.url}/accounts/login/")
        self._requests(page, 1)

        page.get_by_placeholder("Email").fill("michael.scott@dundermifflin.com")
        page.get_by_placeholder("Password").fill("dundermifflin")
        page.get_by_role("button", name="Sign In", exact=True).click()

        page.wait_for_url(f"{live_server.url}/", timeout=10000)

    def test_password_sign_in_survives_a_late_autofill_response(self, page: Page, live_server, user):
        # The autofill's options request keeps its WebAuthn challenge in a new anonymous session. When that response
        # arrived after sign-in's, its session cookie replaced the signed-in one, and the user was signed out again.
        held_options = []
        held_page_loads = []
        state = {"signed_in": False, "released": False}

        def hold_options(route):
            # The server answers now, and the browser gets the answer when the test releases it.
            held_options.append((route, route.fetch()))

        def hold_page_load_after_sign_in(route):
            # Keeps the login page open, after sign-in, until the options response has landed. Sign-in ends by loading
            # the home page, and the login page's requests stop once the new page replaces it.
            if state["signed_in"] and not state["released"]:
                held_page_loads.append(route)
            else:
                route.continue_()

        page.route(re.compile(r".*/_allauth/browser/v1/auth/webauthn/login$"), hold_options)
        page.route(f"{live_server.url}/", hold_page_load_after_sign_in)
        page.on("response", lambda response: response.url.endswith("/auth/login") and state.update(signed_in=True))

        page.goto(f"{live_server.url}/accounts/login/")
        page.get_by_placeholder("Email").fill("michael.scott@dundermifflin.com")
        page.get_by_placeholder("Password").fill("dundermifflin")
        page.get_by_role("button", name="Sign In", exact=True).click()
        # Time for a sign-in that doesn't wait for the options response to finish.
        page.wait_for_timeout(1000)

        state["released"] = True
        for route, response in held_options:
            route.fulfill(response=response)
        for route in held_page_loads:
            route.continue_()

        expect(page.get_by_role("button", name=re.compile(r"^Notifications"))).to_be_visible()
        assert page.request.get(f"{live_server.url}/api/app-context/").json()["user"]
