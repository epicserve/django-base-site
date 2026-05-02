import json

from django.test import TestCase

from apps.accounts.models import User


def _detail_url(pk: int) -> str:
    return f"/api/users/{pk}/"


class TestUserTimezoneAPI(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass",  # noqa: S106
            timezone="America/Chicago",
        )
        self.client.force_login(self.user)

    def test_patch_timezone_valid(self):
        resp = self.client.patch(
            _detail_url(self.user.pk),
            data=json.dumps({"timezone": "America/New_York"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.timezone, "America/New_York")

    def test_patch_timezone_invalid(self):
        resp = self.client.patch(
            _detail_url(self.user.pk),
            data=json.dumps({"timezone": "Invalid/Timezone"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_patch_other_user_forbidden(self):
        other_user = User.objects.create_user(
            username="otheruser",
            password="testpass",  # noqa: S106
        )
        resp = self.client.patch(
            _detail_url(other_user.pk),
            data=json.dumps({"timezone": "America/New_York"}),
            content_type="application/json",
        )
        self.assertIn(resp.status_code, [403, 404])

    def test_get_user_includes_timezone(self):
        resp = self.client.get(_detail_url(self.user.pk))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["timezone"], "America/Chicago")
