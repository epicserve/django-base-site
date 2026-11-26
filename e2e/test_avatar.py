"""End-to-end tests for the profile photo on /accounts/general/, a multipart upload through the typed API client."""

import io

import pytest
from PIL import Image
from playwright.sync_api import Page, expect


def _png() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (64, 64), "teal").save(buffer, "PNG")
    return buffer.getvalue()


class TestAvatar:
    def test_upload_and_remove(self, page: Page, sign_in, user):
        # The e2e settings keep uploads in memory, which nothing serves, and UserAvatar falls back to initials when its
        # image fails to load. So answer requests for the uploaded thumbnail with an image.
        page.route("**/avatars/thumbnails/**", lambda route: route.fulfill(body=_png(), content_type="image/png"))
        sign_in(user, "/accounts/general/")
        # The avatar on the user menu button reads the app store, which the cropper updates after a save or remove.
        header_photo = page.locator('[data-dropdown="nav"] > button img')
        expect(header_photo).to_have_count(0)

        page.get_by_role("button", name="Change Photo").click()
        page.locator('input[type="file"]').set_input_files(
            {"name": "michael.png", "mimeType": "image/png", "buffer": _png()}
        )
        expect(page.locator(".vue-advanced-cropper")).to_be_visible()
        page.get_by_role("button", name="Save", exact=True).click()

        expect(page.get_by_alt_text("Profile photo")).to_be_visible()
        expect(header_photo).to_be_visible()
        user.refresh_from_db()
        assert user.avatar_thumbnail

        page.get_by_role("button", name="Remove").click()

        expect(page.get_by_alt_text("Profile photo")).to_have_count(0)
        expect(header_photo).to_have_count(0)
        user.refresh_from_db()
        assert not user.avatar_thumbnail

    @pytest.mark.parametrize("key", ["Enter", "Space"])
    def test_choose_an_image_with_the_keyboard(self, page: Page, sign_in, user, key):
        # Playwright starts catching file choosers when something listens for them, without waiting until it does.
        # Listening only from `expect_file_chooser()` missed a chooser opened right away about 1 run in 70, so listen
        # from the start.
        page.on("filechooser", lambda chooser: None)
        sign_in(user, "/accounts/general/")
        page.get_by_role("button", name="Change Photo").press("Enter")
        expect(page.get_by_role("dialog", name="Change Profile Photo")).to_be_visible()
        choose_label = page.locator("label", has_text="Choose an Image")
        expect(choose_label).to_have_css("outline-style", "none")

        # The dialog opens with its close button focused, and the file input is the next stop. It used to be
        # `display: none`, which Tab skips, so a keyboard couldn't choose an image.
        page.keyboard.press("Tab")
        expect(page.get_by_label("Choose an Image")).to_be_focused()
        # The input is visually hidden, so its label shows the focus ring.
        expect(choose_label).to_have_css("outline-style", "solid")
        expect(choose_label).to_have_css("outline-width", "2px")

        with page.expect_file_chooser() as file_chooser:
            page.keyboard.press(key)
        file_chooser.value.set_files({"name": "michael.png", "mimeType": "image/png", "buffer": _png()})
        expect(page.locator(".vue-advanced-cropper")).to_be_visible()
