"""End-to-end tests for the profile photo on /accounts/general/, a multipart upload through the typed API client."""

import io
import re

from PIL import Image
from playwright.sync_api import Page, expect


def _png() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (64, 64), "teal").save(buffer, "PNG")
    return buffer.getvalue()


class TestAvatar:
    def _sign_in(self, page: Page, live_server):
        # Sign-in skips `?next=` for /accounts/* pages, so go to the page afterwards.
        page.goto(f"{live_server.url}/accounts/login/")
        page.get_by_placeholder("Email").fill("michael.scott@dundermifflin.com")
        page.get_by_placeholder("Password").fill("dundermifflin")
        page.get_by_role("button", name="Sign In", exact=True).click()
        page.wait_for_url(re.compile(r"^(?!.*/accounts/login/)"), timeout=10000)
        page.goto(f"{live_server.url}/accounts/general/")

    def test_upload_and_remove(self, page: Page, live_server, user):
        self._sign_in(page, live_server)

        page.get_by_role("button", name="Change Photo").click()
        page.locator('input[type="file"]').set_input_files(
            {"name": "michael.png", "mimeType": "image/png", "buffer": _png()}
        )
        expect(page.locator(".vue-advanced-cropper")).to_be_visible()
        page.get_by_role("button", name="Save", exact=True).click()

        expect(page.get_by_alt_text("Profile photo")).to_be_visible()
        user.refresh_from_db()
        assert user.avatar_thumbnail

        page.get_by_role("button", name="Remove").click()

        expect(page.get_by_alt_text("Profile photo")).to_have_count(0)
        user.refresh_from_db()
        assert not user.avatar_thumbnail
