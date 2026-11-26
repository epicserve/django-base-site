import logging
from smtplib import SMTPServerDisconnected

from django.core import mail
from django.core.mail import EmailMessage, EmailMultiAlternatives

import pytest
from kombu.exceptions import OperationalError

from apps.accounts.recipes import make_user
from apps.base.tasks import send_email_message
from apps.base.tests import BaseTest
from apps.base.tests.mail import record_queued_emails, use_failing_mail_server
from apps.base.utils.email import email_to_dict, queue_email, send_email


class TestSendEmail(BaseTest):
    @classmethod
    def setUpTestData(cls):
        cls.sender = make_user("michael@example.com", first_name="Michael", last_name="Scott")
        cls.recipient = make_user("pam@example.com", first_name="Pam", last_name="Beesly")

    @pytest.fixture(autouse=True)
    def _pytest_fixtures(self, monkeypatch):
        self.monkeypatch = monkeypatch

    def test_queues_the_rendered_message_instead_of_sending_it(self):
        queued = record_queued_emails(self.monkeypatch)

        send_email(
            self.sender,
            [self.recipient],
            subject="Test Email",
            base_template_name="emails/test_email",
            context={"date_time": "Nov 21, 2026", "debug_settings": []},
        )

        assert mail.outbox == []
        [message] = queued
        assert message["subject"] == "Test Email"
        assert message["to"] == ["Pam Beesly <pam@example.com>"]
        assert message["headers"] == {"Reply-To": "Michael Scott <michael@example.com>"}
        assert "Nov 21, 2026" in message["body"]
        [[html, mimetype]] = message["alternatives"]
        assert mimetype == "text/html"
        assert "Nov 21, 2026" in html


class TestQueueEmail:
    def test_the_task_sends_the_message_as_built(self, mailoutbox):
        message = EmailMultiAlternatives(
            "Subject",
            "Text body",
            "from@example.com",
            ["to@example.com"],
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
            reply_to=["reply@example.com"],
            headers={"X-Test": "1"},
        )
        message.attach_alternative("<p>HTML body</p>", "text/html")

        send_email_message(email_to_dict(message))

        [sent] = mailoutbox
        assert (sent.subject, sent.body, sent.from_email) == ("Subject", "Text body", "from@example.com")
        assert (sent.to, sent.cc, sent.bcc, sent.reply_to) == (
            ["to@example.com"],
            ["cc@example.com"],
            ["bcc@example.com"],
            ["reply@example.com"],
        )
        assert sent.extra_headers == {"X-Test": "1"}
        assert [tuple(alternative) for alternative in sent.alternatives] == [("<p>HTML body</p>", "text/html")]

    def test_the_task_keeps_an_html_only_message_html(self, mailoutbox):
        # allauth builds an HTML-only EmailMessage when a template has no .txt version.
        message = EmailMessage("Subject", "<p>HTML body</p>", "from@example.com", ["to@example.com"])
        message.content_subtype = "html"

        send_email_message(email_to_dict(message))

        assert mailoutbox[0].content_subtype == "html"

    def test_the_task_retries_a_transport_error_before_giving_up(self, settings, monkeypatch):
        backend = use_failing_mail_server(settings)
        # Test settings propagate task errors, which would raise the first retry instead of running it.
        monkeypatch.setitem(send_email_message.app.conf, "task_eager_propagates", False)
        message = EmailMessage("Subject", "Body", "from@example.com", ["to@example.com"])

        # Run eagerly, each retry runs at once rather than after its backoff.
        result = send_email_message.apply(args=[email_to_dict(message)])

        assert result.state == "FAILURE"
        assert isinstance(result.result, SMTPServerDisconnected)
        assert backend.attempts == send_email_message.max_retries + 1

    def test_a_broker_outage_is_logged_not_raised(self, monkeypatch, caplog):
        def broker_down(*args, **kwargs):
            raise OperationalError("Error 111 connecting to redis:6379. Connection refused.")

        monkeypatch.setattr("celery.app.task.Task.apply_async", broker_down)
        message = EmailMessage("Welcome", "Body", "from@example.com", ["to@example.com"])

        with caplog.at_level(logging.ERROR, logger="apps.base.utils.email"):
            queue_email(message)

        assert "Couldn't queue the email 'Welcome'" in caplog.text

    def test_attachments_are_refused(self):
        message = EmailMessage("Subject", "Body", "from@example.com", ["to@example.com"])
        message.attach("report.txt", "contents", "text/plain")

        with pytest.raises(ValueError, match="attachments"):
            queue_email(message)
