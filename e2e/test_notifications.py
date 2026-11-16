"""End-to-end tests for /notifications/: what the page changes shows up in the unread count straight away."""

import re

from django.utils import timezone

import pytest
from playwright.sync_api import Page, expect


def _sign_in(page: Page, live_server, next_path: str):
    page.goto(f"{live_server.url}/accounts/login/?next={next_path}")
    page.get_by_placeholder("Email").fill("michael.scott@dundermifflin.com")
    page.get_by_placeholder("Password").fill("dundermifflin")
    page.get_by_role("button", name="Sign In", exact=True).click()
    page.wait_for_url(re.compile(r"^(?!.*/accounts/login/)"), timeout=10000)


class TestUnreadCount:
    # The header bell and the page's Unread tab both show the count, which otherwise refreshes on a 20-second poll.
    # These assertions use Playwright's 5-second default timeout, so the poll can't make them pass.

    @pytest.fixture(autouse=True)
    def _notifications(self, user):
        from apps.notifications.models import Notification
        from apps.notifications.services import notify

        for title in ("Report Due", "Meeting Moved", "Party Planning"):
            notify([user], title=title)
        (read,) = notify([user], title="Old News")
        Notification.objects.filter(pk=read.pk).update(read_at=timezone.now())

    def _open(self, page: Page, live_server):
        _sign_in(page, live_server, "/notifications/")
        expect(page.get_by_role("button", name="Notifications, 3 unread")).to_be_visible()

    def _select(self, page: Page, row: str):
        page.get_by_role("button", name="Select", exact=True).click()
        page.get_by_role("button", name=row, exact=True).get_by_role("checkbox").click()

    def _expect_unread(self, page: Page, count: int):
        expect(page.get_by_role("button", name=f"Notifications, {count} unread")).to_be_visible()
        expect(page.get_by_role("button", name=f"Unread {count}", exact=True)).to_be_visible()

    @pytest.mark.parametrize("action", ["Mark Read", "Delete"])
    def test_bulk_action_on_unread(self, page: Page, live_server, action):
        self._open(page, live_server)
        self._select(page, "Unread, Report Due")
        page.get_by_role("button", name=action, exact=True).click()
        self._expect_unread(page, 2)

    def test_bulk_mark_unread(self, page: Page, live_server):
        self._open(page, live_server)
        self._select(page, "Old News")
        page.get_by_role("button", name="Mark Unread", exact=True).click()
        self._expect_unread(page, 4)
        # The user marked it unread, so the refresh mustn't announce it as a new notification.
        expect(page.get_by_role("region", name="Notifications (F8)").get_by_text("Old News")).to_have_count(0)

    def test_delete(self, page: Page, live_server):
        self._open(page, live_server)
        row = page.get_by_role("button", name="Unread, Report Due", exact=True)
        row.hover()
        row.get_by_role("button", name="Delete Notification").click()
        self._expect_unread(page, 2)

    def test_open(self, page: Page, live_server):
        # A notification without a URL opens in a dialog and is marked read.
        self._open(page, live_server)
        page.get_by_role("button", name="Unread, Report Due", exact=True).click()
        dialog = page.get_by_role("dialog", name="Report Due")
        expect(dialog).to_be_visible()
        page.keyboard.press("Escape")
        expect(dialog).to_be_hidden()
        self._expect_unread(page, 2)
        expect(page.get_by_role("button", name="Report Due", exact=True)).to_be_visible()
