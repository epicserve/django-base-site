import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from allauth.headless import app_settings


class Command(BaseCommand):
    help = (
        "Export django-allauth's headless OpenAPI spec as JSON, matching the installed version and configured flows "
        "(run by `just generate_api_types` with --settings=config.settings.api_types)."
    )

    def add_arguments(self, parser):
        parser.add_argument("--output", default=None, help="Write the spec to this file instead of stdout.")

    def handle(self, *args, **options):
        if not app_settings.SERVE_SPECIFICATION:
            raise CommandError("Set HEADLESS_SERVE_SPECIFICATION = True (config.settings.api_types does).")

        # Not a public allauth API; the drift check in `just lint` fails if its output changes.
        from allauth.headless.spec.internal.schema import get_schema

        result = json.dumps(get_schema(), indent=2, sort_keys=True, default=str)
        if options["output"]:
            Path(options["output"]).write_text(result + "\n")
        else:
            self.stdout.write(result)
