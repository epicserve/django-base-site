from django.test import override_settings

import pytest

from apps.accounts.recipes import make_user
from apps.base.tests import BaseTest
from apps.base.tests.mail import record_queued_emails
from apps.notifications.email import send_email
from apps.notifications.models import NotificationPreference
from apps.notifications.recipes import COMMENTS_CATEGORY


@override_settings(NOTIFICATIONS_CATEGORIES=[COMMENTS_CATEGORY])
class TestSendEmail(BaseTest):
    @classmethod
    def setUpTestData(cls):
        cls.pam = make_user("pam@example.com", first_name="Pam", last_name="Beesly")
        cls.jim = make_user("jim@example.com", first_name="Jim", last_name="Halpert")
        NotificationPreference.objects.create(user=cls.jim, category="comments", in_app=True, email=False)

    @pytest.fixture(autouse=True)
    def _pytest_fixtures(self, monkeypatch):
        self.monkeypatch = monkeypatch

    def _send(self, recipients):
        send_email(
            None,
            recipients,
            subject="New Comment",
            base_template_name="emails/test_email",
            context={"date_time": "Nov 21, 2026", "debug_settings": []},
            category="comments",
        )

    def test_leaves_out_users_who_turned_off_email_for_the_category(self):
        queued = record_queued_emails(self.monkeypatch)

        self._send([self.pam, self.jim])

        [message] = queued
        assert message["to"] == ["Pam Beesly <pam@example.com>"]

    def test_sends_nothing_when_every_recipient_turned_it_off(self):
        queued = record_queued_emails(self.monkeypatch)

        self._send([self.jim])

        assert queued == []
