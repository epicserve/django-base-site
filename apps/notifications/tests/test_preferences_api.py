import json
import logging

from django.test import override_settings

from apps.accounts.recipes import make_user
from apps.base.tests import BaseTest
from apps.notifications.models import NotificationPreference
from apps.notifications.recipes import COMMENTS_CATEGORY

PREFS_URL = "/api/notifications/preferences/"


def _detail(category: str) -> str:
    return f"/api/notifications/preferences/{category}/"


@override_settings(NOTIFICATIONS_CATEGORIES=[COMMENTS_CATEGORY])
class TestPreferencesAPI(BaseTest):
    @classmethod
    def setUpTestData(cls):
        cls.user = make_user()

    def setUp(self):
        # These tests make 4xx responses on purpose; keep django.request's warnings about them out of the output.
        logger = logging.getLogger("django.request")
        self.addCleanup(logger.setLevel, logger.level)
        logger.setLevel(logging.ERROR)
        self.sign_in(self.user)

    def _patch(self, url, data):
        return self.client.patch(url, data=json.dumps(data), content_type="application/json")

    def test_list_returns_registered_categories_with_defaults(self):
        resp = self.client.get(PREFS_URL)
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 1
        assert body[0]["key"] == "comments"
        assert body[0]["in_app"] is True
        assert body[0]["email"] is True

    def test_list_returns_empty_when_no_categories(self):
        with self.settings(NOTIFICATIONS_CATEGORIES=[]):
            resp = self.client.get(PREFS_URL)
        assert resp.json() == []

    def test_patch_creates_preference_row(self):
        resp = self._patch(_detail("comments"), {"email": False})
        assert resp.status_code == 200
        assert resp.json()["email"] is False
        pref = NotificationPreference.objects.get(user=self.user, category="comments")
        assert pref.email is False
        assert pref.in_app is True

    def test_patch_updates_existing_row(self):
        NotificationPreference.objects.create(user=self.user, category="comments", in_app=True, email=True)
        resp = self._patch(_detail("comments"), {"in_app": False})
        assert resp.status_code == 200
        pref = NotificationPreference.objects.get(user=self.user, category="comments")
        assert pref.in_app is False
        assert pref.email is True

    def test_patch_unknown_category_returns_404(self):
        resp = self._patch(_detail("nonexistent"), {"email": False})
        assert resp.status_code == 404

    def test_requires_login(self):
        self.client.logout()
        resp = self.client.get(PREFS_URL)
        assert resp.status_code in (401, 403)
