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


def send_email(sending_user, recipients: list, subject: str, base_template_name: str, context: dict):
    context["subject"] = subject
    user_model = get_user_model()

    if isinstance(recipients[0], user_model):
        recipients = [get_user_email(user) for user in recipients]

    text_message = render_to_string(f"{base_template_name}.txt", context=context)
    html_message = render_to_string(f"{base_template_name}.html", context=context)
    headers = {"Reply-To": get_user_email(sending_user)}
    mail = EmailMultiAlternatives(subject, text_message, settings.DEFAULT_FROM_EMAIL, recipients, headers=headers)
    mail.attach_alternative(html_message, "text/html")
    mail.send()
