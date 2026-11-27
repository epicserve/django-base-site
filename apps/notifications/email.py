from apps.base.utils import email
from apps.notifications.categories import filter_recipients
from apps.notifications.constants import NotificationChannel


def send_email(
    sending_user,
    recipients: list,
    subject: str,
    base_template_name: str,
    context: dict,
    category: str,
):
    """
    Send a notification email, leaving out the users who turned off email for `category`.

    The same as `apps.base.utils.email.send_email`, which knows nothing about notification categories (apps.base
    imports no other app), plus the user's preference. `recipients` is a list of User instances: a list of email
    strings has no preferences to read, so pass it to `apps.base.utils.email.send_email` instead. The in-app side is
    `notify()`, which reads the same preferences.
    """
    recipients = filter_recipients(recipients, category, NotificationChannel.EMAIL)
    if not recipients:
        return
    email.send_email(sending_user, recipients, subject, base_template_name, context)
