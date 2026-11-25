"""End-to-end tests for /notifications/: changes show up in the unread count and the page's list straight away."""

import re

from django.utils import timezone

import pytest
from playwright.sync_api import Page, expect


@pytest.fixture()
def notifications(user):
    from apps.notifications.models import Notification
    from apps.notifications.services import notify

    for title in ("Report Due", "Meeting Moved", "Party Planning"):
        notify([user], title=title)
    (read,) = notify([user], title="Old News")
    Notification.objects.filter(pk=read.pk).update(read_at=timezone.now())


@pytest.fixture()
def open_page(page: Page, sign_in, user):
    """Open /notifications/ signed in as `user`, once its list and the bell's unread count have loaded."""

    def _open_page():
        sign_in(user, "/notifications/")
        expect(page.get_by_role("button", name="Notifications, 3 unread")).to_be_visible()
        expect(page.get_by_role("main").get_by_role("button", name="Unread, Report Due", exact=True)).to_be_visible()

    return _open_page


@pytest.mark.usefixtures("notifications")
class TestUnreadCount:
    # The header bell and the page's Unread tab both show the count, which otherwise refreshes on a 20-second poll.
    # These assertions use Playwright's 5-second default timeout, so the poll can't make them pass.

    def _select(self, page: Page, row: str):
        page.get_by_role("button", name="Select", exact=True).click()
        page.get_by_role("button", name=row, exact=True).get_by_role("checkbox").click()

    def _expect_unread(self, page: Page, count: int):
        expect(page.get_by_role("button", name=f"Notifications, {count} unread")).to_be_visible()
        expect(page.get_by_role("button", name=f"Unread {count}", exact=True)).to_be_visible()

    @pytest.mark.parametrize("action", ["Mark Read", "Delete"])
    def test_bulk_action_on_unread(self, page: Page, open_page, action):
        open_page()
        self._select(page, "Unread, Report Due")
        page.get_by_role("button", name=action, exact=True).click()
        self._expect_unread(page, 2)

    def test_bulk_mark_unread(self, page: Page, open_page):
        open_page()
        self._select(page, "Old News")
        page.get_by_role("button", name="Mark Unread", exact=True).click()
        self._expect_unread(page, 4)
        # The user marked it unread, so the refresh mustn't announce it as a new notification.
        expect(page.get_by_role("region", name="Notifications (F8)").get_by_text("Old News")).to_have_count(0)

    def test_delete(self, page: Page, open_page):
        open_page()
        row = page.get_by_role("button", name="Unread, Report Due", exact=True)
        row.hover()
        row.get_by_role("button", name="Delete Notification").click()
        self._expect_unread(page, 2)

    def test_open(self, page: Page, open_page):
        # A notification without a URL opens in a dialog and is marked read.
        open_page()
        page.get_by_role("button", name="Unread, Report Due", exact=True).click()
        dialog = page.get_by_role("dialog", name="Report Due")
        expect(dialog).to_be_visible()
        page.keyboard.press("Escape")
        expect(dialog).to_be_hidden()
        self._expect_unread(page, 2)
        expect(page.get_by_role("button", name="Report Due", exact=True)).to_be_visible()


@pytest.mark.usefixtures("notifications")
class TestPageFollowsBell:
    # The page keeps its own copy of the list, which has to follow what the bell in the header changes.

    def _open_bell(self, page: Page, open_page):
        open_page()
        page.get_by_role("button", name="Notifications, 3 unread").click()
        return page.get_by_role("navigation")

    def test_open(self, page: Page, open_page):
        bell = self._open_bell(page, open_page)
        bell.get_by_role("button", name="Unread, Report Due", exact=True).click()
        dialog = page.get_by_role("dialog", name="Report Due")
        expect(dialog).to_be_visible()
        page.keyboard.press("Escape")
        expect(dialog).to_be_hidden()
        expect(page.get_by_role("main").get_by_role("button", name="Report Due", exact=True)).to_be_visible()

    def test_delete(self, page: Page, open_page):
        bell = self._open_bell(page, open_page)
        row = bell.get_by_role("button", name="Unread, Report Due", exact=True)
        row.hover()
        row.get_by_role("button", name="Delete Notification").click()
        expect(page.get_by_role("main").get_by_role("button", name=re.compile("Report Due"))).to_have_count(0)

    def test_bulk_mark_read(self, page: Page, open_page):
        bell = self._open_bell(page, open_page)
        bell.get_by_role("button", name="Select", exact=True).click()
        bell.get_by_role("button", name="Unread, Report Due", exact=True).get_by_role("checkbox").click()
        bell.get_by_role("button", name="Mark Read", exact=True).click()
        expect(page.get_by_role("main").get_by_role("button", name="Report Due", exact=True)).to_be_visible()

    def test_mark_all_read(self, page: Page, open_page):
        bell = self._open_bell(page, open_page)
        bell.get_by_role("button", name="Mark All Read", exact=True).click()
        expect(page.get_by_role("main").get_by_role("button", name=re.compile(r"^Unread, "))).to_have_count(0)


@pytest.mark.usefixtures("notifications")
class TestNewNotifications:
    def test_show_on_the_page(self, page: Page, open_page, user):
        from apps.notifications.services import notify

        page.clock.install()
        open_page()

        notify([user], title="Pretzel Day")
        # The bell polls every 20 seconds.
        page.clock.fast_forward("00:21")
        expect(page.get_by_role("button", name="Notifications, 4 unread")).to_be_visible()

        expect(page.get_by_role("main").get_by_role("button", name="Unread, Pretzel Day", exact=True)).to_be_visible()
