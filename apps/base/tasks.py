from botocore.exceptions import BotoCoreError, ClientError
from celery import shared_task

from apps.base.utils.email import email_from_dict


# Transport errors: smtplib's errors, socket errors and timeouts are all OSError; SES (django-ses) raises botocore's.
# Retry n waits a random time up to 5s * 2^n, capped at 10 minutes: up to about 20 minutes over all 8 retries, so a
# mail server that's down for a while still gets the email once it's back.
@shared_task(
    autoretry_for=(OSError, BotoCoreError, ClientError),
    retry_backoff=5,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=8,
)
def send_email_message(message: dict) -> None:
    """Send a message that `apps.base.utils.email.queue_email` serialized."""
    email_from_dict(message).send()
