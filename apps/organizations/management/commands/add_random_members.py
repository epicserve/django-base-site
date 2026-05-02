import random

from django.apps import apps
from django.conf import settings
from django.core.management import BaseCommand

from apps.organizations.models import Organization, OrganizationMember

user_model = apps.get_model(settings.AUTH_USER_MODEL)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--org-slug", type=str, required=True, help="The organization's slug that you want to add fake user to."
        )
        parser.add_argument("--number", type=int, default=10, help="Number members to create.")

    def handle(self, **options):
        org = Organization.objects.get(slug=options["org_slug"])
        for _i in range(options["number"]):
            user_model = apps.get_model(settings.AUTH_USER_MODEL)
            user = user_model.objects.filter(is_superuser=False).order_by("?").first()
            is_owner = random.choice([True, False])  # noqa: S311
            OrganizationMember.objects.create(
                organization=org,
                user=user,
                is_owner=is_owner,
            )
