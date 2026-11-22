"""Helpers for testing email, which `apps.base.utils.email.queue_email` hands to a Celery task."""

from smtplib import SMTPServerDisconnected

from django.core.mail.backends.base import BaseEmailBackend


class FailingEmailBackend(BaseEmailBackend):
    """A mail server that's down: every send raises, and `attempts` counts them."""

    attempts = 0

    def send_messages(self, email_messages):
        type(self).attempts += 1
        raise SMTPServerDisconnected("Connection unexpectedly closed")


def use_failing_mail_server(settings) -> type[FailingEmailBackend]:
    """Point the default mailer at `FailingEmailBackend` for one test (pass pytest's `settings` fixture)."""
    FailingEmailBackend.attempts = 0
    settings.MAILERS = {"default": {"BACKEND": f"{__name__}.FailingEmailBackend"}}
    return FailingEmailBackend


def record_queued_emails(monkeypatch) -> list[dict]:
    """
    Stand in for the broker, as in production: queued tasks are recorded instead of run, so nothing is sent.

    Test settings run tasks eagerly. This patches Celery's `Task.apply_async` rather than the email task, so on code
    that sends inline it patches nothing and the send still happens in the request.
    """
    queued: list[dict] = []

    def apply_async(task, args: tuple = (), kwargs=None, **options):
        assert task.name == "apps.base.tasks.send_email_message", f"Unexpected task {task.name}"
        queued.append(args[0])

    monkeypatch.setattr("celery.app.task.Task.apply_async", apply_async)
    return queued
