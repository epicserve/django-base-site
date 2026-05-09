import json
import logging

from django.contrib.auth import user_logged_in

import pytest

from apps.accounts.models import User
from apps.notifications.constants import NotificationChannel
from apps.notifications.models import NotificationPreference
from apps.organizations.signals import user_logged_in_receiver

PREFS_URL = "/api/notifications/preferences/"

COMMENTS_CATEGORY = {
    "key": "comments",
    "label": "Comments",
    "description": "Replies to your posts.",
    "default_channels": (NotificationChannel.IN_APP, NotificationChannel.EMAIL),
}


def _detail(category: str) -> str:
    return f"/api/notifications/preferences/{category}/"


@pytest.mark.django_db
class TestPreferencesAPI:
    @pytest.fixture(autouse=True)
    def _setup(self, db, client, settings):
        logging.getLogger("django.request").setLevel(logging.ERROR)
        user_logged_in.disconnect(user_logged_in_receiver)
        try:
            settings.NOTIFICATIONS_CATEGORIES = [COMMENTS_CATEGORY]
            self.user = User.objects.create_user(username="alice", password="secret")  # noqa: S106
            self.client = client
            self.client.force_login(self.user)
            yield
        finally:
            user_logged_in.connect(user_logged_in_receiver)

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

    def test_list_returns_empty_when_no_categories(self, settings):
        settings.NOTIFICATIONS_CATEGORIES = []
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
