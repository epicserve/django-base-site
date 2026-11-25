import json
import logging

from django.utils import timezone

from apps.accounts.tests.recipes import make_user
from apps.base.tests import BaseTest
from apps.base.tests.sign_in import sign_in
from apps.notifications.models import Notification
from apps.notifications.tests.recipes import make_notification
from apps.organizations.tests.recipes import make_member, make_org

LIST_URL = "/api/notifications/"
UNREAD_URL = "/api/notifications/unread-count/"
BULK_URL = "/api/notifications/bulk/"


def _detail_url(pk: int) -> str:
    return f"/api/notifications/{pk}/"


class TestNotificationAPI(BaseTest):
    @classmethod
    def setUpTestData(cls):
        cls.user = make_user("alice@example.com")
        cls.other_user = make_user("bob@example.com")
        # Signing in selects `org`, the user's primary organization.
        cls.org = make_org(cls.user)
        make_member(cls.org, cls.other_user)
        cls.other_org = make_org(cls.user)

    def setUp(self):
        # These tests make 4xx responses on purpose; keep django.request's warnings about them out of the output.
        logger = logging.getLogger("django.request")
        self.addCleanup(logger.setLevel, logger.level)
        logger.setLevel(logging.ERROR)

    def _make(self, quantity: int, recipient=None, org=None, **fields) -> list[Notification]:
        """Make `quantity` notifications for `recipient` (default: the user) in `org` (default: the selected org)."""
        return [
            make_notification(recipient or self.user, organization=org or self.org, **fields) for _ in range(quantity)
        ]

    def _post_json(self, url, data):
        return self.client.post(url, data=json.dumps(data), content_type="application/json")

    def _patch_json(self, url, data):
        return self.client.patch(url, data=json.dumps(data), content_type="application/json")

    def test_requires_login(self):
        resp = self.client.get(LIST_URL)
        assert resp.status_code in (401, 403)

    def test_list_scopes_to_user_and_org(self):
        self._make(2, title="mine in org")
        self._make(1, org=self.other_org, title="mine in other")
        self._make(1, recipient=self.other_user, title="bob's")

        sign_in(self.client, self.user)
        resp = self.client.get(LIST_URL)
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] == 2
        for row in body["results"]:
            assert row["title"] == "mine in org"

    def test_unread_count(self):
        self._make(3)
        self._make(2, read_at=timezone.now())
        sign_in(self.client, self.user)
        resp = self.client.get(UNREAD_URL)
        assert resp.status_code == 200
        assert resp.json()["count"] == 3

    def test_filter_unread(self):
        self._make(2)
        self._make(1, read_at=timezone.now())
        sign_in(self.client, self.user)
        resp = self.client.get(LIST_URL, {"is_read": "false"})
        assert resp.json()["count"] == 2
        resp = self.client.get(LIST_URL, {"is_read": "true"})
        assert resp.json()["count"] == 1

    def test_mark_read_sets_read_at(self):
        [n] = self._make(1)
        assert n.read_at is None
        sign_in(self.client, self.user)
        resp = self._patch_json(_detail_url(n.pk), {"is_read": True})
        assert resp.status_code == 200
        n.refresh_from_db()
        assert n.read_at is not None
        self._patch_json(_detail_url(n.pk), {"is_read": False})
        n.refresh_from_db()
        assert n.read_at is None

    def test_delete_one(self):
        [n] = self._make(1)
        sign_in(self.client, self.user)
        resp = self.client.delete(_detail_url(n.pk))
        assert resp.status_code == 204
        assert Notification.objects.count() == 0

    def test_cannot_act_on_other_users_notification(self):
        [n] = self._make(1, recipient=self.other_user)
        sign_in(self.client, self.user)
        resp = self.client.delete(_detail_url(n.pk))
        assert resp.status_code == 404
        assert Notification.objects.count() == 1

    def test_bulk_mark_read_by_ids(self):
        unread = self._make(3)
        sign_in(self.client, self.user)
        ids = [n.pk for n in unread[:2]]
        resp = self._post_json(BULK_URL, {"action": "mark_read", "ids": ids})
        assert resp.status_code == 200
        assert resp.json()["updated"] == 2
        assert Notification.objects.filter(read_at__isnull=True).count() == 1

    def test_bulk_mark_all_unread(self):
        self._make(3)
        self._make(2, recipient=self.other_user)
        sign_in(self.client, self.user)
        resp = self._post_json(BULK_URL, {"action": "mark_read", "all_unread": True})
        assert resp.status_code == 200
        assert resp.json()["updated"] == 3
        assert Notification.objects.filter(recipient=self.user, read_at__isnull=True).count() == 0
        assert Notification.objects.filter(recipient=self.other_user, read_at__isnull=True).count() == 2

    def test_bulk_delete(self):
        mine = self._make(3)
        self._make(1, recipient=self.other_user)
        sign_in(self.client, self.user)
        ids = [n.pk for n in mine]
        resp = self._post_json(BULK_URL, {"action": "delete", "ids": ids})
        assert resp.status_code == 200
        assert resp.json()["deleted"] == 3
        assert Notification.objects.count() == 1

    def test_bulk_delete_cannot_touch_other_users(self):
        [theirs] = self._make(1, recipient=self.other_user)
        sign_in(self.client, self.user)
        resp = self._post_json(BULK_URL, {"action": "delete", "ids": [theirs.pk]})
        assert resp.status_code == 200
        assert resp.json()["deleted"] == 0
        assert Notification.objects.filter(pk=theirs.pk).exists()

    def test_bulk_requires_valid_action(self):
        sign_in(self.client, self.user)
        resp = self._post_json(BULK_URL, {"action": "nonsense", "ids": [1]})
        assert resp.status_code == 400

    def test_bulk_requires_ids_when_not_all_unread(self):
        sign_in(self.client, self.user)
        resp = self._post_json(BULK_URL, {"action": "mark_read"})
        assert resp.status_code == 400
