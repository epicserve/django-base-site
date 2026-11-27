"""
End-to-end tests for the impersonation banner shown above the nav while a superuser impersonates someone.

Hiding it lasts until the next impersonation starts, even for the same user.
"""

import pytest
from playwright.sync_api import Page, expect


@pytest.fixture()
def superuser(db):
    from apps.accounts.recipes import make_superuser

    return make_superuser("leslie.knope@pawnee.example", username="leslie", first_name="Leslie", last_name="Knope")


def _banner(page: Page):
    return page.get_by_role("status").filter(has_text="Impersonating")


def _impersonate(page: Page, live_server, name: str, *, open_search: bool = True):
    if open_search:
        page.goto(f"{live_server.url}/impersonate/")
    # The search matches first name, last name, username, or email, one field at a time.
    page.locator("#search").fill(name.split()[0])
    page.locator("tbody tr").filter(has_text=name).click()
    page.wait_for_url(f"{live_server.url}/")


class TestImpersonationBanner:
    def test_banner_shows_who_is_impersonated(self, page: Page, live_server, sign_in, superuser, user):
        sign_in(superuser, "/")
        expect(page.get_by_role("heading", level=1)).to_be_visible()
        expect(_banner(page)).to_have_count(0)

        _impersonate(page, live_server, "Michael Scott")

        expect(_banner(page)).to_contain_text("Michael Scott")
        expect(page.locator("#djhj")).to_have_count(0)

    def test_hide_lasts_until_the_next_impersonation(self, page: Page, live_server, sign_in, superuser, user):
        sign_in(superuser, "/impersonate/")
        _impersonate(page, live_server, "Michael Scott", open_search=False)

        # The banner hides at once, before the POST that saves it in the session finishes;
        # reloading before then can cancel the request, and the banner comes back.
        with page.expect_response("**/api/impersonation/hide-banner/"):
            _banner(page).get_by_role("button", name="Hide Banner").click()
        expect(_banner(page)).to_have_count(0)
        page.reload()
        expect(page.get_by_role("heading", level=1)).to_be_visible()
        expect(_banner(page)).to_have_count(0)

        page.get_by_role("button", name="User Menu", exact=True).click()
        page.get_by_role("button", name="Stop Impersonating").click()
        page.wait_for_url(f"{live_server.url}/")
        _impersonate(page, live_server, "Michael Scott")

        expect(_banner(page)).to_contain_text("Michael Scott")

    def test_stop_impersonating_from_the_banner(self, page: Page, live_server, sign_in, superuser, user):
        sign_in(superuser, "/impersonate/")
        _impersonate(page, live_server, "Michael Scott", open_search=False)

        _banner(page).get_by_role("button", name="Stop Impersonating").click()
        page.wait_for_url(f"{live_server.url}/")

        expect(page.get_by_role("heading", name="Hi Leslie", exact=False)).to_be_visible()
        expect(_banner(page)).to_have_count(0)
