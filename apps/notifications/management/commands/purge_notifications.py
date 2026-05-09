from django.core.management.base import BaseCommand

from apps.notifications.tasks import purge_expired


class Command(BaseCommand):
    help = "Delete expired notifications (run by celery beat in production)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=None,
            help="Override NOTIFICATIONS_RETENTION_DAYS for this run (e.g. --days 0 to purge everything).",
        )

    def handle(self, *args, **options):
        deleted = purge_expired(days=options["days"])
        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted} notification(s)."))
