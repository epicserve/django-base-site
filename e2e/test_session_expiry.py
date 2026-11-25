"""
When a signed-in user's session ends, their next API call sends them to sign in again, then back to where they were.

Before, the call failed with a 401 and the page stayed as it was, with an error or nothing new, until a reload showed
the sign-in page and lost their place.
"""

import re

from playwright.sync_api import Page, expect


def _sign_in(page: Page):
    page.get_by_placeholder("Email").fill("michael.scott@dundermifflin.com")
    page.get_by_placeholder("Password").fill("dundermifflin")
    page.get_by_role("button", name="Sign In", exact=True).click()


class TestWhenTheSessionEnds:
    def test_the_next_api_call_sends_you_to_sign_in_and_back(self, page: Page, live_server, user):
        from django.contrib.sessions.models import Session

        page.goto(f"{live_server.url}/accounts/login/?next=/notifications/")
        _sign_in(page)
        page.wait_for_url(f"{live_server.url}/notifications/", timeout=10000)
        expect(page.get_by_role("button", name=re.compile(r"^Notifications"))).to_be_visible()

        Session.objects.all().delete()
        # Coming back to the tab refreshes the unread count, which calls the API.
        page.evaluate("document.dispatchEvent(new Event('visibilitychange'))")

        page.wait_for_url(f"{live_server.url}/accounts/login/?next=%2Fnotifications%2F&session=expired", timeout=10000)
        expect(page.get_by_role("status")).to_have_text(
            "Your session has ended. Sign in again to pick up where you left off."
        )

        _sign_in(page)

        page.wait_for_url(f"{live_server.url}/notifications/", timeout=10000)

    def test_signing_in_normally_shows_no_notice(self, page: Page, live_server, user):
        page.goto(f"{live_server.url}/accounts/login/?next=/notifications/")

        expect(page.get_by_role("button", name="Sign In", exact=True)).to_be_visible()
        expect(page.get_by_text("Your session has ended")).to_have_count(0)
