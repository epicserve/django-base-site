"""End-to-end tests for where the SPA leaves the scroll position when it changes pages."""

import pytest
from playwright.sync_api import Page, expect

# Short enough that the home page and the account page both scroll.
VIEWPORT = {"width": 1280, "height": 300}

ROUTER_PUSH = "path => document.querySelector('#app').__vue_app__.config.globalProperties.$router.push(path)"


class TestScrollOnNavigation:
    @pytest.fixture(autouse=True)
    def _sign_in(self, page: Page, sign_in, user):
        page.set_viewport_size(VIEWPORT)
        sign_in(user, "/")
        expect(self._included(page)).to_be_attached()

    @staticmethod
    def _included(page: Page):
        return page.get_by_role("heading", name="What's in the Box")

    @staticmethod
    def _scroll_to(page: Page, top: int):
        page.evaluate("top => window.scrollTo(0, top)", top)
        page.wait_for_function("top => window.scrollY === top", arg=top, timeout=5000)

    @staticmethod
    def _scroll_y(page: Page) -> int:
        return page.evaluate("window.scrollY")

    @staticmethod
    def _bottom(page: Page) -> int:
        """Return how far down the page can scroll."""
        return page.evaluate("document.documentElement.scrollHeight - window.innerHeight")

    def _open_account_settings(self, page: Page, live_server):
        # dispatch_event() rather than click(), which scrolls the link into view first and so scrolls the page itself.
        page.locator('nav a[href="/accounts/general/"]').first.dispatch_event("click")
        page.wait_for_url(f"{live_server.url}/accounts/general/")
        expect(page.get_by_label("First Name", exact=True)).to_be_visible()

    def test_a_new_page_opens_at_the_top(self, page: Page, live_server):
        # The account page is tall enough to stay scrolled this far, which it did.
        self._scroll_to(page, 150)

        self._open_account_settings(page, live_server)

        assert self._scroll_y(page) == 0

    def test_back_returns_to_where_you_were(self, page: Page, live_server):
        self._open_account_settings(page, live_server)
        account_bottom = self._bottom(page)
        page.go_back()
        expect(self._included(page)).to_be_attached()
        # Further down than the account page goes, so the position can't carry over from it. The position is only
        # reachable once the home page has replaced the account page.
        top = account_bottom + 100
        assert top <= self._bottom(page)
        self._scroll_to(page, top)
        self._open_account_settings(page, live_server)

        page.go_back()

        page.wait_for_url(f"{live_server.url}/")
        page.wait_for_function("top => window.scrollY === top", arg=top, timeout=5000)

    def test_a_hash_scrolls_to_its_element_on_load(self, page: Page, live_server):
        page.goto(f"{live_server.url}/#home-included")

        expect(self._included(page)).to_be_in_viewport()
        assert self._scroll_y(page) > 0

    def test_a_hash_scrolls_to_its_element_after_changing_pages(self, page: Page, live_server):
        self._open_account_settings(page, live_server)

        page.evaluate(ROUTER_PUSH, "/#home-included")

        page.wait_for_url(f"{live_server.url}/#home-included")
        expect(self._included(page)).to_be_in_viewport()
        assert self._scroll_y(page) > 0

    def test_a_query_change_keeps_the_scroll_position(self, page: Page, live_server):
        # A change to the query alone, like a filter or a page of results, keeps the same page on screen.
        self._scroll_to(page, 300)

        page.evaluate(ROUTER_PUSH, "/?tab=teams")

        page.wait_for_url(f"{live_server.url}/?tab=teams")
        page.wait_for_timeout(500)
        assert self._scroll_y(page) == 300
