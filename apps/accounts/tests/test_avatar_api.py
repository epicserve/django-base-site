import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from PIL import Image

from apps.accounts.models import User

URL = "/api/avatar/"


def _make_png_bytes(size=(512, 512), color="red"):
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format="PNG")
    return buf.getvalue()


class TestAvatarAPI(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user",
            email="user@example.com",
            password="secret",  # noqa: S106
        )

    def test_upload_avatar(self):
        self.client.force_login(self.user)
        upload = SimpleUploadedFile("avatar.png", _make_png_bytes(), content_type="image/png")
        resp = self.client.post(URL, {"image": upload})
        self.assertEqual(resp.status_code, 200)
        self.assertIn("avatar_url", resp.json())
        self.user.refresh_from_db()
        self.assertTrue(bool(self.user.avatar_thumbnail))

    def test_delete_avatar(self):
        self.client.force_login(self.user)
        upload = SimpleUploadedFile("avatar.png", _make_png_bytes(), content_type="image/png")
        self.client.post(URL, {"image": upload})
        self.user.refresh_from_db()
        self.assertTrue(bool(self.user.avatar_thumbnail))

        resp = self.client.delete(URL)
        self.assertEqual(resp.status_code, 204)
        self.user.refresh_from_db()
        self.assertFalse(bool(self.user.avatar_thumbnail))
        self.assertFalse(bool(self.user.avatar_original))
