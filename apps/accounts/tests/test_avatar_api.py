import io

from django.core.files.uploadedfile import SimpleUploadedFile

from PIL import Image

from apps.accounts.recipes import make_user
from apps.base.tests import BaseTest
from apps.base.tests.sign_in import sign_in

URL = "/api/avatar/"


def _make_png_bytes(size=(512, 512), color="red"):
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format="PNG")
    return buf.getvalue()


class TestAvatarAPI(BaseTest):
    @classmethod
    def setUpTestData(cls):
        cls.user = make_user("user@example.com")

    def setUp(self):
        sign_in(self.client, self.user)
        self.addCleanup(self._delete_avatar_files)

    def _delete_avatar_files(self):
        # Rolling back the test's transaction leaves the uploaded files in storage.
        self.user.refresh_from_db()
        for image in (self.user.avatar_original, self.user.avatar_thumbnail):
            if image:
                image.delete(save=False)

    def test_upload_avatar(self):
        upload = SimpleUploadedFile("avatar.png", _make_png_bytes(), content_type="image/png")
        resp = self.client.post(URL, {"image": upload})
        assert resp.status_code == 200
        assert "avatar_url" in resp.json()
        self.user.refresh_from_db()
        assert self.user.avatar_thumbnail

    def test_delete_avatar(self):
        upload = SimpleUploadedFile("avatar.png", _make_png_bytes(), content_type="image/png")
        self.client.post(URL, {"image": upload})
        self.user.refresh_from_db()
        assert self.user.avatar_thumbnail

        resp = self.client.delete(URL)
        assert resp.status_code == 204
        self.user.refresh_from_db()
        assert not self.user.avatar_thumbnail
        assert not self.user.avatar_original
