"""End-to-end test that the superuser's "Mailpit" and "Silo Admin" menu links open this stack's consoles."""

import re

import pytest
from playwright.sync_api import Page, expect


@pytest.fixture()
def superuser(db):
    from apps.accounts.recipes import make_superuser

    return make_superuser("leslie.knope@pawnee.example", username="leslie", first_name="Leslie", last_name="Knope")


class TestDevToolLinks:
    def test_links_use_this_stacks_ports(self, page: Page, sign_in, superuser, settings):
        # A git worktree's stack publishes them on its own host ports (scripts/worktree), not on 8025 and 9001.
        settings.MAILPIT_PORT = 8031
        settings.SILO_CONSOLE_PORT = 9013
        sign_in(superuser, "/")

        page.get_by_role("button", name="User Menu", exact=True).click()

        # On the host the app was opened on.
        mailpit = page.get_by_role("link", name="Mailpit", exact=True)
        expect(mailpit).to_have_attribute("href", re.compile(r"^http://[^/]+:8031/$"))
        expect(page.get_by_role("link", name="Silo Admin", exact=True)).to_have_attribute(
            "href", re.compile(r"^http://[^/]+:9013/$")
        )
