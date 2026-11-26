import json

from apps.accounts.recipes import make_user
from apps.base.tests import BaseTest


def _detail_url(pk: int) -> str:
    return f"/api/users/{pk}/"


class TestUserTimezoneAPI(BaseTest):
    @classmethod
    def setUpTestData(cls):
        cls.user = make_user("testuser@example.com", timezone="America/Chicago")

    def setUp(self):
        self.sign_in(self.user)

    def test_patch_timezone_valid(self):
        resp = self.client.patch(
            _detail_url(self.user.pk),
            data=json.dumps({"timezone": "America/New_York"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        self.user.refresh_from_db()
        assert self.user.timezone == "America/New_York"

    def test_patch_timezone_invalid(self):
        resp = self.client.patch(
            _detail_url(self.user.pk),
            data=json.dumps({"timezone": "Invalid/Timezone"}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_patch_other_user_forbidden(self):
        other_user = make_user("otheruser@example.com")
        resp = self.client.patch(
            _detail_url(other_user.pk),
            data=json.dumps({"timezone": "America/New_York"}),
            content_type="application/json",
        )
        assert resp.status_code in (403, 404)

    def test_get_user_includes_timezone(self):
        resp = self.client.get(_detail_url(self.user.pk))
        assert resp.status_code == 200
        assert resp.json()["timezone"] == "America/Chicago"
