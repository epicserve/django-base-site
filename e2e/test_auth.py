import re

import pytest
from playwright.sync_api import Page, expect


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


class TestLogout:
    @pytest.mark.usefixtures("_login")
    def test_logout_redirects_to_login(self, page: Page, live_server):
        page.goto(f"{live_server.url}/accounts/logout/")

        page.wait_for_url(re.compile(r"/accounts/login"), timeout=10000)
        expect(page.get_by_placeholder("Email")).to_be_visible()
        expect(page.get_by_role("button", name="Sign In", exact=True)).to_be_visible()


class TestAuthRedirects:
    def test_unauthenticated_user_redirected_to_login(self, page: Page, live_server):
        page.goto(f"{live_server.url}/accounts/general/")

        expect(page).to_have_url(re.compile(r"/accounts/login"))
        expect(page.get_by_placeholder("Email")).to_be_visible()
