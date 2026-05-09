import json
import logging

from django.contrib.auth import user_logged_in

import pytest
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


@pytest.mark.django_db
class TestNotificationAPI:
    @pytest.fixture(autouse=True)
    def _setup(self, db, client):
        logging.getLogger("django.request").setLevel(logging.ERROR)
        user_logged_in.disconnect(user_logged_in_receiver)
        try:
            self.client = client
            self.user = User.objects.create_user(username="alice", password="secret")  # noqa: S106
            self.other_user = User.objects.create_user(username="bob", password="secret")  # noqa: S106
            self.org = baker.make("organizations.Organization")
            self.other_org = baker.make("organizations.Organization")
            yield
        finally:
            user_logged_in.connect(user_logged_in_receiver)

    def _login_in_org(self, user=None, org=None):
        self.client.force_login(user or self.user)
        set_session_org(self.client, org or self.org)

    def _post_json(self, url, data):
        return self.client.post(url, data=json.dumps(data), content_type="application/json")

    def _patch_json(self, url, data):
        return self.client.patch(url, data=json.dumps(data), content_type="application/json")

    def test_requires_login(self):
        resp = self.client.get(LIST_URL)
        assert resp.status_code in (401, 403)

    def test_list_scopes_to_user_and_org(self):
        baker.make(Notification, recipient=self.user, organization=self.org, title="mine in org", _quantity=2)
        baker.make(Notification, recipient=self.user, organization=self.other_org, title="mine in other")
        baker.make(Notification, recipient=self.other_user, organization=self.org, title="bob's")

        self._login_in_org()
        resp = self.client.get(LIST_URL)
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] == 2
        for row in body["results"]:
            assert row["title"] == "mine in org"

    def test_unread_count(self):
        baker.make(Notification, recipient=self.user, organization=self.org, _quantity=3)
        baker.make(
            Notification,
            recipient=self.user,
            organization=self.org,
            read_at="2026-01-01T00:00:00Z",
            _quantity=2,
        )
        self._login_in_org()
        resp = self.client.get(UNREAD_URL)
        assert resp.status_code == 200
        assert resp.json()["count"] == 3

    def test_filter_unread(self):
        baker.make(Notification, recipient=self.user, organization=self.org, _quantity=2)
        baker.make(Notification, recipient=self.user, organization=self.org, read_at="2026-01-01T00:00:00Z")
        self._login_in_org()
        resp = self.client.get(LIST_URL, {"is_read": "false"})
        assert resp.json()["count"] == 2
        resp = self.client.get(LIST_URL, {"is_read": "true"})
        assert resp.json()["count"] == 1

    def test_mark_read_sets_read_at(self):
        n = baker.make(Notification, recipient=self.user, organization=self.org)
        assert n.read_at is None
        self._login_in_org()
        resp = self._patch_json(_detail_url(n.pk), {"is_read": True})
        assert resp.status_code == 200
        n.refresh_from_db()
        assert n.read_at is not None
        self._patch_json(_detail_url(n.pk), {"is_read": False})
        n.refresh_from_db()
        assert n.read_at is None

    def test_delete_one(self):
        n = baker.make(Notification, recipient=self.user, organization=self.org)
        self._login_in_org()
        resp = self.client.delete(_detail_url(n.pk))
        assert resp.status_code == 204
        assert Notification.objects.count() == 0

    def test_cannot_act_on_other_users_notification(self):
        n = baker.make(Notification, recipient=self.other_user, organization=self.org)
        self._login_in_org()
        resp = self.client.delete(_detail_url(n.pk))
        assert resp.status_code == 404
        assert Notification.objects.count() == 1

    def test_bulk_mark_read_by_ids(self):
        unread = baker.make(Notification, recipient=self.user, organization=self.org, _quantity=3)
        self._login_in_org()
        ids = [n.pk for n in unread[:2]]
        resp = self._post_json(BULK_URL, {"action": "mark_read", "ids": ids})
        assert resp.status_code == 200
        assert resp.json()["updated"] == 2
        assert Notification.objects.filter(read_at__isnull=True).count() == 1

    def test_bulk_mark_all_unread(self):
        baker.make(Notification, recipient=self.user, organization=self.org, _quantity=3)
        baker.make(Notification, recipient=self.other_user, organization=self.org, _quantity=2)
        self._login_in_org()
        resp = self._post_json(BULK_URL, {"action": "mark_read", "all_unread": True})
        assert resp.status_code == 200
        assert resp.json()["updated"] == 3
        assert Notification.objects.filter(recipient=self.user, read_at__isnull=True).count() == 0
        assert Notification.objects.filter(recipient=self.other_user, read_at__isnull=True).count() == 2

    def test_bulk_delete(self):
        mine = baker.make(Notification, recipient=self.user, organization=self.org, _quantity=3)
        baker.make(Notification, recipient=self.other_user, organization=self.org)
        self._login_in_org()
        ids = [n.pk for n in mine]
        resp = self._post_json(BULK_URL, {"action": "delete", "ids": ids})
        assert resp.status_code == 200
        assert resp.json()["deleted"] == 3
        assert Notification.objects.count() == 1

    def test_bulk_delete_cannot_touch_other_users(self):
        theirs = baker.make(Notification, recipient=self.other_user, organization=self.org)
        self._login_in_org()
        resp = self._post_json(BULK_URL, {"action": "delete", "ids": [theirs.pk]})
        assert resp.status_code == 200
        assert resp.json()["deleted"] == 0
        assert Notification.objects.filter(pk=theirs.pk).exists()

    def test_bulk_requires_valid_action(self):
        self._login_in_org()
        resp = self._post_json(BULK_URL, {"action": "nonsense", "ids": [1]})
        assert resp.status_code == 400

    def test_bulk_requires_ids_when_not_all_unread(self):
        self._login_in_org()
        resp = self._post_json(BULK_URL, {"action": "mark_read"})
        assert resp.status_code == 400
