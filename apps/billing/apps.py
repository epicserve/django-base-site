from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class BillingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.billing"
    verbose_name = "Billing"

    def ready(self):
        if not getattr(settings, "BILLING_ENABLED", False):
            return
        self._validate_settings()
        self._configure_stripe()
        # Import for the side effect of connecting @receiver-decorated handlers.
        from apps.billing import signals  # noqa: F401

    @staticmethod
    def _validate_settings():
        from apps.billing.plans import get_plans

        if not settings.STRIPE_SECRET_KEY:
            raise ImproperlyConfigured("BILLING_ENABLED is True but STRIPE_SECRET_KEY is empty.")
        if not settings.STRIPE_WEBHOOK_SECRET:
            raise ImproperlyConfigured("BILLING_ENABLED is True but STRIPE_WEBHOOK_SECRET is empty.")
        for plan in get_plans():
            if plan.is_free:
                continue
            if not (plan.monthly_price_id or plan.annual_price_id):
                raise ImproperlyConfigured(
                    f"BILLING_PLANS plan {plan.key!r} has no monthly_price_id or annual_price_id. "
                    f"Set at least one Stripe price ID, or mark the plan with is_free=True."
                )

    @staticmethod
    def _configure_stripe():
        import stripe

        stripe.api_key = settings.STRIPE_SECRET_KEY
        # Pin the Stripe API version so SDK bumps don't silently shift webhook payloads.
        stripe.api_version = "2024-10-28.acacia"
