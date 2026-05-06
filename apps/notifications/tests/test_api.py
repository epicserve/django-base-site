import json
import logging

from django.contrib.auth import user_logged_in
from django.test import TestCase

from model_bakery import baker

from apps.accounts.models import User
from apps.notifications.models import Notification
from apps.organizations.signals import user_logged_in_receiver

LIST_URL = "/api/notifications/"
UNREAD_URL = "/api/notifications/unread-count/"
BULK_URL = "/api/notifications/bulk/"


def _detail_url(pk: int) -> str:
    return f"/api/notifications/{pk}/"


def set_session_org(client, org):
    session = client.session
    session["organization_data"] = json.dumps(
        {"pk": org.pk, "id": org.pk, "name": org.name, "slug": org.slug, "is_owner": False}
    )
    session.save()


class TestNotificationAPI(TestCase):
    @classmethod
    def setUpClass(cls):
        logging.getLogger("django.request").setLevel(logging.ERROR)
        user_logged_in.disconnect(user_logged_in_receiver)
        super().setUpClass()

    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="secret")  # noqa: S106
        self.other_user = User.objects.create_user(username="bob", password="secret")  # noqa: S106
        self.org = baker.make("organizations.Organization")
        self.other_org = baker.make("organizations.Organization")

    def _login_in_org(self, user=None, org=None):
        self.client.force_login(user or self.user)
        set_session_org(self.client, org or self.org)

    def _post_json(self, url, data):
        return self.client.post(url, data=json.dumps(data), content_type="application/json")

    def _patch_json(self, url, data):
        return self.client.patch(url, data=json.dumps(data), content_type="application/json")

    def test_requires_login(self):
        resp = self.client.get(LIST_URL)
        self.assertIn(resp.status_code, (401, 403))

    def test_list_scopes_to_user_and_org(self):
        baker.make(
            Notification, recipient=self.user, organization=self.org, type="mention", title="mine in org", _quantity=2
        )
        baker.make(
            Notification, recipient=self.user, organization=self.other_org, type="mention", title="mine in other"
        )
        baker.make(Notification, recipient=self.other_user, organization=self.org, type="mention", title="bob's")

        self._login_in_org()
        resp = self.client.get(LIST_URL)
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["count"], 2)
        for row in body["results"]:
            self.assertEqual(row["title"], "mine in org")

    def test_unread_count(self):
        baker.make(Notification, recipient=self.user, organization=self.org, type="mention", _quantity=3)
        baker.make(
            Notification,
            recipient=self.user,
            organization=self.org,
            type="mention",
            read_at="2026-01-01T00:00:00Z",
            _quantity=2,
        )
        self._login_in_org()
        resp = self.client.get(UNREAD_URL)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["count"], 3)

    def test_filter_unread(self):
        baker.make(Notification, recipient=self.user, organization=self.org, type="mention", _quantity=2)
        baker.make(
            Notification, recipient=self.user, organization=self.org, type="mention", read_at="2026-01-01T00:00:00Z"
        )
        self._login_in_org()
        resp = self.client.get(LIST_URL, {"is_read": "false"})
        self.assertEqual(resp.json()["count"], 2)
        resp = self.client.get(LIST_URL, {"is_read": "true"})
        self.assertEqual(resp.json()["count"], 1)

    def test_mark_read_sets_read_at(self):
        n = baker.make(Notification, recipient=self.user, organization=self.org, type="mention")
        self.assertIsNone(n.read_at)
        self._login_in_org()
        resp = self._patch_json(_detail_url(n.pk), {"is_read": True})
        self.assertEqual(resp.status_code, 200)
        n.refresh_from_db()
        self.assertIsNotNone(n.read_at)
        self._patch_json(_detail_url(n.pk), {"is_read": False})
        n.refresh_from_db()
        self.assertIsNone(n.read_at)

    def test_delete_one(self):
        n = baker.make(Notification, recipient=self.user, organization=self.org, type="mention")
        self._login_in_org()
        resp = self.client.delete(_detail_url(n.pk))
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(Notification.objects.count(), 0)

    def test_cannot_act_on_other_users_notification(self):
        n = baker.make(Notification, recipient=self.other_user, organization=self.org, type="mention")
        self._login_in_org()
        resp = self.client.delete(_detail_url(n.pk))
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(Notification.objects.count(), 1)

    def test_bulk_mark_read_by_ids(self):
        unread = baker.make(Notification, recipient=self.user, organization=self.org, type="mention", _quantity=3)
        self._login_in_org()
        ids = [n.pk for n in unread[:2]]
        resp = self._post_json(BULK_URL, {"action": "mark_read", "ids": ids})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["updated"], 2)
        self.assertEqual(Notification.objects.filter(read_at__isnull=True).count(), 1)

    def test_bulk_mark_all_unread(self):
        baker.make(Notification, recipient=self.user, organization=self.org, type="mention", _quantity=3)
        baker.make(Notification, recipient=self.other_user, organization=self.org, type="mention", _quantity=2)
        self._login_in_org()
        resp = self._post_json(BULK_URL, {"action": "mark_read", "all_unread": True})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["updated"], 3)
        self.assertEqual(Notification.objects.filter(recipient=self.user, read_at__isnull=True).count(), 0)
        self.assertEqual(Notification.objects.filter(recipient=self.other_user, read_at__isnull=True).count(), 2)

    def test_bulk_delete(self):
        mine = baker.make(Notification, recipient=self.user, organization=self.org, type="mention", _quantity=3)
        baker.make(Notification, recipient=self.other_user, organization=self.org, type="mention")
        self._login_in_org()
        ids = [n.pk for n in mine]
        resp = self._post_json(BULK_URL, {"action": "delete", "ids": ids})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["deleted"], 3)
        self.assertEqual(Notification.objects.count(), 1)

    def test_bulk_delete_cannot_touch_other_users(self):
        theirs = baker.make(Notification, recipient=self.other_user, organization=self.org, type="mention")
        self._login_in_org()
        resp = self._post_json(BULK_URL, {"action": "delete", "ids": [theirs.pk]})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["deleted"], 0)
        self.assertTrue(Notification.objects.filter(pk=theirs.pk).exists())

    def test_bulk_requires_valid_action(self):
        self._login_in_org()
        resp = self._post_json(BULK_URL, {"action": "nonsense", "ids": [1]})
        self.assertEqual(resp.status_code, 400)

    def test_bulk_requires_ids_when_not_all_unread(self):
        self._login_in_org()
        resp = self._post_json(BULK_URL, {"action": "mark_read"})
        self.assertEqual(resp.status_code, 400)
