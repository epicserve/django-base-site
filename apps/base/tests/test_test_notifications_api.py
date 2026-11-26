import json
import logging

from apps.accounts.recipes import make_superuser, make_user
from apps.base.tests import BaseTest
from apps.notifications.models import Notification
from apps.organizations.recipes import make_member, make_org

URL = "/api/test-notifications/"


class TestSendTestNotification(BaseTest):
    @classmethod
    def setUpTestData(cls):
        cls.sender = make_superuser("root@example.com")
        cls.recipient = make_user("alice@example.com", is_staff=True)
        cls.org = make_org(cls.sender, name="Acme")

    def setUp(self):
        # Keep the 400 responses' warnings out of the test output.
        logger = logging.getLogger("django.request")
        self.addCleanup(logger.setLevel, logger.level)
        logger.setLevel(logging.ERROR)
        self.sign_in(self.sender, self.org)

    def _post(self, data):
        return self.client.post(URL, data=json.dumps(data), content_type="application/json")

    def test_rejects_when_recipient_not_in_sender_org(self):
        resp = self._post({"user_id": self.recipient.pk, "send_email": False, "send_in_app": True})
        assert resp.status_code == 400
        assert "Acme" in resp.json()["detail"]
        assert Notification.objects.count() == 0

    def test_succeeds_when_recipient_is_in_sender_org(self):
        make_member(self.org, self.recipient)
        resp = self._post({"user_id": self.recipient.pk, "send_email": False, "send_in_app": True})
        assert resp.status_code == 200
        assert Notification.objects.filter(recipient=self.recipient).count() == 1
