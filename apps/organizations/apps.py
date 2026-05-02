from django.apps import AppConfig


class OrganizationsConfig(AppConfig):
    name = "apps.organizations"

    def ready(self):
        from . import signals

        assert signals  # noqa: S101
