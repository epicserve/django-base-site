from email.utils import formataddr

from django.apps import apps
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


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
    category: str = "",
):
    """
    Send a templated multipart email.

    When `category` is set and `recipients` is a list of User instances,
    recipients with the email channel disabled for that category are filtered
    out (see apps.notifications.categories.should_send). When `recipients` is
    a list of email strings, no filtering is done — the caller is responsible
    for honoring preferences.
    """
    context["subject"] = subject
    user_model = get_user_model()

    if recipients and isinstance(recipients[0], user_model):
        if category:
            from apps.notifications.categories import filter_recipients
            from apps.notifications.constants import NotificationChannel

            recipients = filter_recipients(recipients, category, NotificationChannel.EMAIL)
        if not recipients:
            return
        recipients = [get_user_email(user) for user in recipients]

    text_message = render_to_string(f"{base_template_name}.txt", context=context)
    html_message = render_to_string(f"{base_template_name}.html", context=context)
    headers = {"Reply-To": get_user_email(sending_user)}
    mail = EmailMultiAlternatives(subject, text_message, settings.DEFAULT_FROM_EMAIL, recipients, headers=headers)
    mail.attach_alternative(html_message, "text/html")
    mail.send()
