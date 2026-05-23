"""
Tests for the Stripe webhook dispatcher.

These bypass `stripe.Webhook.construct_event` by monkeypatching it — the
library's HMAC verification is third-party code we trust. What matters here
is our idempotency + bounded-retry logic and that the right handler is
invoked for each event type.
"""

import json

from django.test import RequestFactory

import pytest
from model_bakery import baker

from apps.billing.constants import WEBHOOK_MAX_FAILURES, SubscriptionStatus
from apps.billing.models import BillingCustomer, Subscription, WebhookEvent


@pytest.fixture
def billing_settings(settings):
    settings.BILLING_ENABLED = True
    settings.STRIPE_SECRET_KEY = "sk_test_dummy"  # noqa: S105
    settings.STRIPE_WEBHOOK_SECRET = "whsec_dummy"  # noqa: S105
    settings.BILLING_PLANS = [
        {"key": "free", "name": "Free", "is_free": True, "is_default": True, "features": {}},
        {
            "key": "pro",
            "name": "Pro",
            "monthly_price_id": "price_pro_monthly",
            "annual_price_id": "price_pro_annual",
            "features": {},
        },
    ]
    settings.BILLING_FEATURES = []
    return settings


def _post(event: dict):
    """Build a POST request that the webhook view will accept."""
    body = json.dumps(event).encode()
    return RequestFactory().post(
        "/webhooks/stripe/",
        data=body,
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE="t=0,v1=fake",
    )


@pytest.fixture
def patch_construct_event(monkeypatch):
    """Make stripe.Webhook.construct_event a pass-through that returns the parsed body."""

    def _factory(event_payload: dict):
        def _construct(payload, sig_header, secret):
            return event_payload

        monkeypatch.setattr("stripe.Webhook.construct_event", _construct)

    return _factory


@pytest.mark.django_db
class TestWebhookIdempotency:
    def test_replay_returns_200_without_reprocessing(self, billing_settings, patch_construct_event):
        org = baker.make("organizations.Organization")
        BillingCustomer.objects.create(organization=org, stripe_customer_id="cus_replay")
        event = {
            "id": "evt_replay",
            "type": "customer.subscription.updated",
            "data": {"object": {"id": "sub_x", "customer": "cus_replay"}},
        }
        patch_construct_event(event)

        from apps.billing.webhooks import stripe_webhook

        # First delivery — handler runs, marker stored.
        first = stripe_webhook(_post(event))
        assert first.status_code == 200
        marker = WebhookEvent.objects.get(stripe_event_id="evt_replay")
        first_processed_at = marker.processed_at
        assert first_processed_at is not None

        # Second delivery — should short-circuit on IntegrityError + processed_at.
        second = stripe_webhook(_post(event))
        assert second.status_code == 200
        marker.refresh_from_db()
        # processed_at unchanged proves we didn't re-run the handler path.
        assert marker.processed_at == first_processed_at

    def test_unknown_event_type_marks_processed(self, billing_settings, patch_construct_event):
        event = {"id": "evt_unknown", "type": "totally.made.up", "data": {"object": {}}}
        patch_construct_event(event)

        from apps.billing.webhooks import stripe_webhook

        response = stripe_webhook(_post(event))
        assert response.status_code == 200
        marker = WebhookEvent.objects.get(stripe_event_id="evt_unknown")
        assert marker.processed_at is not None
        assert marker.failure_count == 0

    def test_invalid_signature_returns_400(self, billing_settings, monkeypatch):
        import stripe

        def _raise(payload, sig_header, secret):
            raise stripe.error.SignatureVerificationError("nope", sig_header)

        monkeypatch.setattr("stripe.Webhook.construct_event", _raise)

        from apps.billing.webhooks import stripe_webhook

        response = stripe_webhook(_post({"id": "evt_bad"}))
        assert response.status_code == 400
        assert not WebhookEvent.objects.exists()


@pytest.mark.django_db
class TestWebhookBoundedRetry:
    def _raising_event(self, monkeypatch):
        """Wire up a customer.subscription.updated event whose handler raises."""

        def _explode(stripe_subscription):
            raise RuntimeError("boom")

        monkeypatch.setattr("apps.billing.webhooks.sync_subscription_from_stripe", _explode)
        return {
            "id": "evt_fail",
            "type": "customer.subscription.updated",
            "data": {"object": {"id": "sub_y", "customer": "cus_y"}},
        }

    def test_failure_bumps_count_and_returns_500(self, billing_settings, patch_construct_event, monkeypatch):
        event = self._raising_event(monkeypatch)
        patch_construct_event(event)

        from apps.billing.webhooks import stripe_webhook

        response = stripe_webhook(_post(event))
        assert response.status_code == 500
        marker = WebhookEvent.objects.get(stripe_event_id="evt_fail")
        assert marker.processed_at is None
        assert marker.failure_count == 1
        assert "boom" in marker.last_error

    def test_marker_persists_across_failures(self, billing_settings, patch_construct_event, monkeypatch):
        event = self._raising_event(monkeypatch)
        patch_construct_event(event)

        from apps.billing.webhooks import stripe_webhook

        for _ in range(3):
            stripe_webhook(_post(event))

        # One marker total — failures don't churn rows.
        assert WebhookEvent.objects.filter(stripe_event_id="evt_fail").count() == 1
        marker = WebhookEvent.objects.get(stripe_event_id="evt_fail")
        assert marker.failure_count == 3
        assert marker.processed_at is None

    def test_gives_up_after_max_failures(self, billing_settings, patch_construct_event, monkeypatch):
        event = self._raising_event(monkeypatch)
        patch_construct_event(event)

        from apps.billing.webhooks import stripe_webhook

        # Climb to MAX - 1 failures with 500 responses.
        for _ in range(WEBHOOK_MAX_FAILURES - 1):
            response = stripe_webhook(_post(event))
            assert response.status_code == 500

        # The MAX'th delivery still runs the handler (it raises), bumps the
        # counter to MAX, then returns 200 because we've hit the ceiling.
        response = stripe_webhook(_post(event))
        assert response.status_code == 200
        marker = WebhookEvent.objects.get(stripe_event_id="evt_fail")
        assert marker.failure_count == WEBHOOK_MAX_FAILURES

        # Any further delivery hits the IntegrityError + give-up branch and
        # never re-invokes the handler — counter must not advance.
        response = stripe_webhook(_post(event))
        assert response.status_code == 200
        marker.refresh_from_db()
        assert marker.failure_count == WEBHOOK_MAX_FAILURES


@pytest.mark.django_db
class TestSubscriptionDeletedHandler:
    def test_marks_subscription_canceled(self, billing_settings, patch_construct_event, monkeypatch):
        org = baker.make("organizations.Organization")
        BillingCustomer.objects.create(organization=org, stripe_customer_id="cus_del")
        sub = Subscription.objects.create(
            organization=org,
            stripe_subscription_id="sub_del",
            plan_key="pro",
            status=SubscriptionStatus.ACTIVE,
        )

        # Don't actually send emails or notify in this test — the handler imports
        # them lazily, so we monkeypatch the symbols at the point of use.
        monkeypatch.setattr("apps.notifications.services.notify", lambda *a, **kw: [])
        monkeypatch.setattr("apps.base.utils.email.send_email", lambda *a, **kw: None)

        event = {
            "id": "evt_del",
            "type": "customer.subscription.deleted",
            "data": {"object": {"id": "sub_del"}},
        }
        patch_construct_event(event)

        from apps.billing.webhooks import stripe_webhook

        response = stripe_webhook(_post(event))
        assert response.status_code == 200

        sub.refresh_from_db()
        assert sub.status == SubscriptionStatus.CANCELED
        assert sub.canceled_at is not None
