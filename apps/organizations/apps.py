from importlib import import_module

from django.apps import AppConfig


class OrganizationsConfig(AppConfig):
    name = "apps.organizations"

    def ready(self):
        # Import for the side effect of connecting @receiver-decorated handlers.
        import_module("apps.organizations.signals")
