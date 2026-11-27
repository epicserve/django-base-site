import logging
from email.utils import formataddr

from django.apps import apps
from django.conf import settings
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template.loader import render_to_string

from kombu.exceptions import OperationalError

logger = logging.getLogger(__name__)


def get_user_model():
    """Return the active user model."""
    return apps.get_model(settings.AUTH_USER_MODEL)


def get_user_email(user):
    user_name = user.get_full_name() or user.username
    return formataddr((user_name, user.email))


def send_email(
    sending_user,
    recipients: list,
    subject: str,
    base_template_name: str,
    context: dict,
):
    """
    Render a templated multipart email and queue it for a Celery worker to send (see `queue_email`).

    `recipients` is a list of User instances or of email strings. To leave out the users who turned off email for a
    notification category, send it with `apps.notifications.email.send_email` instead.
    """
    context["subject"] = subject
    user_model = get_user_model()

    if recipients and isinstance(recipients[0], user_model):
        recipients = [get_user_email(user) for user in recipients]

    text_message = render_to_string(f"{base_template_name}.txt", context=context)
    html_message = render_to_string(f"{base_template_name}.html", context=context)
    headers = {"Reply-To": get_user_email(sending_user)} if sending_user is not None else {}
    mail = EmailMultiAlternatives(subject, text_message, settings.DEFAULT_FROM_EMAIL, recipients, headers=headers)
    mail.attach_alternative(html_message, "text/html")
    queue_email(mail)


def queue_email(message: EmailMessage) -> None:
    """
    Send a built message from a Celery worker (`apps.base.tasks.send_email_message`) instead of this process.

    A mail server that's down or slow can't fail or hold up the request or task that sent the email: the worker
    retries with backoff. The message is already rendered, so the task gets only strings, and a row that changes
    after this call doesn't change what's sent. If the broker can't take the task, the error is logged, not raised.
    """
    from apps.base.tasks import send_email_message

    try:
        send_email_message.delay(email_to_dict(message))
    except OperationalError:
        logger.exception("Couldn't queue the email %r", message.subject)


def email_to_dict(message: EmailMessage) -> dict:
    """Serialize a message to JSON-safe values for `email_from_dict`. Attachments aren't supported."""
    if message.attachments:
        raise ValueError("queue_email() doesn't support attachments.")
    return {
        "subject": message.subject,
        "body": message.body,
        "from_email": message.from_email,
        "to": list(message.to),
        "cc": list(message.cc),
        "bcc": list(message.bcc),
        "reply_to": list(message.reply_to),
        "headers": dict(message.extra_headers),
        "content_subtype": message.content_subtype,
        "alternatives": [[content, mimetype] for content, mimetype in getattr(message, "alternatives", [])],
    }


def email_from_dict(data: dict) -> EmailMultiAlternatives:
    message = EmailMultiAlternatives(
        data["subject"],
        data["body"],
        data["from_email"],
        data["to"],
        cc=data["cc"],
        bcc=data["bcc"],
        reply_to=data["reply_to"],
        headers=data["headers"],
    )
    message.content_subtype = data["content_subtype"]
    for content, mimetype in data["alternatives"]:
        message.attach_alternative(content, mimetype)
    return message
