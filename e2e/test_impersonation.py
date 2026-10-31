"""
End-to-end tests for the impersonation banner shown above the nav while a superuser impersonates someone.

Hiding it lasts until the next impersonation starts, even for the same user.
"""

import re

import pytest
from playwright.sync_api import Page, expect


@pytest.fixture()
def superuser(db):
    from allauth.account.models import EmailAddress

    from apps.accounts.models import User

    superuser = User.objects.create_superuser(
        username="leslie",
        email="leslie.knope@pawnee.example",
        password="dundermifflin",  # noqa: S106
        first_name="Leslie",
        last_name="Knope",
    )
    EmailAddress.objects.create(user=superuser, email=superuser.email, verified=True, primary=True)
    return superuser


def _banner(page: Page):
    return page.get_by_role("status").filter(has_text="Impersonating")


def _sign_in(page: Page, live_server, email: str):
    page.goto(f"{live_server.url}/accounts/login/")
    page.get_by_placeholder("Email").fill(email)
    page.get_by_placeholder("Password").fill("dundermifflin")
    page.get_by_role("button", name="Sign In", exact=True).click()
    page.wait_for_url(re.compile(r"^(?!.*/accounts/login/)"), timeout=10000)


def _impersonate(page: Page, live_server, name: str):
    page.goto(f"{live_server.url}/impersonate/")
    # The search matches first name, last name, username, or email, one field at a time.
    page.locator("#search").fill(name.split()[0])
    page.locator("tbody tr").filter(has_text=name).click()
    page.wait_for_url(f"{live_server.url}/")


class TestImpersonationBanner:
    def test_banner_shows_who_is_impersonated(self, page: Page, live_server, superuser, user):
        _sign_in(page, live_server, superuser.email)
        expect(page.get_by_role("heading", level=1)).to_be_visible()
        expect(_banner(page)).to_have_count(0)

        _impersonate(page, live_server, "Michael Scott")

        expect(_banner(page)).to_contain_text("Michael Scott")
        expect(page.locator("#djhj")).to_have_count(0)

    def test_hide_lasts_until_the_next_impersonation(self, page: Page, live_server, superuser, user):
        _sign_in(page, live_server, superuser.email)
        _impersonate(page, live_server, "Michael Scott")

        _banner(page).get_by_role("button", name="Hide Banner").click()
        expect(_banner(page)).to_have_count(0)
        page.reload()
        expect(page.get_by_role("heading", level=1)).to_be_visible()
        expect(_banner(page)).to_have_count(0)

        page.locator('nav .relative[data-dropdown="nav"]').last.locator("button").first.click()
        page.get_by_role("button", name="Stop Impersonating").click()
        page.wait_for_url(f"{live_server.url}/")
        _impersonate(page, live_server, "Michael Scott")

        expect(_banner(page)).to_contain_text("Michael Scott")

    def test_stop_impersonating_from_the_banner(self, page: Page, live_server, superuser, user):
        _sign_in(page, live_server, superuser.email)
        _impersonate(page, live_server, "Michael Scott")

        _banner(page).get_by_role("button", name="Stop Impersonating").click()
        page.wait_for_url(f"{live_server.url}/")

        expect(page.get_by_role("heading", name="Hi Leslie", exact=False)).to_be_visible()
        expect(_banner(page)).to_have_count(0)
