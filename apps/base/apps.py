from django.apps import AppConfig


class BaseConfig(AppConfig):
    name = "apps.base"

    def ready(self):
        # Here rather than in settings, so test settings can turn it off: every settings module runs _base.py first.
        from apps.base.sentry import init_sentry

        init_sentry()
