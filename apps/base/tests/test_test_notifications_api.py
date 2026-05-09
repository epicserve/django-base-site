import json
import logging

from django.contrib.auth import user_logged_in

import pytest
from model_bakery import baker

from apps.accounts.models import User
from apps.notifications.models import Notification
from apps.organizations.models import OrganizationMember
from apps.organizations.signals import user_logged_in_receiver

URL = "/api/test-notifications/"


def _set_session_org(client, org):
    session = client.session
    session["organization_data"] = json.dumps(
        {"pk": org.pk, "id": org.pk, "name": org.name, "slug": org.slug, "is_owner": False}
    )
    session.save()


@pytest.mark.django_db
class TestSendTestNotification:
    @pytest.fixture(autouse=True)
    def _setup(self, db, client):
        logging.getLogger("django.request").setLevel(logging.ERROR)
        user_logged_in.disconnect(user_logged_in_receiver)
        try:
            self.client = client
            self.sender = User.objects.create_superuser(
                username="root",
                email="root@example.com",
                password="secret",  # noqa: S106
                is_staff=True,
            )
            self.recipient = User.objects.create_user(
                username="alice",
                email="alice@example.com",
                password="secret",  # noqa: S106
                is_staff=True,
            )
            self.org = baker.make("organizations.Organization", name="Acme")
            OrganizationMember.objects.create(organization=self.org, user=self.sender, is_owner=True)
            self.client.force_login(self.sender)
            _set_session_org(self.client, self.org)
            yield
        finally:
            user_logged_in.connect(user_logged_in_receiver)

    def _post(self, data):
        return self.client.post(URL, data=json.dumps(data), content_type="application/json")

    def test_rejects_when_recipient_not_in_sender_org(self):
        resp = self._post({"user_id": self.recipient.pk, "send_email": False, "send_in_app": True})
        assert resp.status_code == 400
        assert "Acme" in resp.json()["detail"]
        assert Notification.objects.count() == 0

    def test_succeeds_when_recipient_is_in_sender_org(self):
        OrganizationMember.objects.create(organization=self.org, user=self.recipient)
        resp = self._post({"user_id": self.recipient.pk, "send_email": False, "send_in_app": True})
        assert resp.status_code == 200
        assert Notification.objects.filter(recipient=self.recipient).count() == 1
