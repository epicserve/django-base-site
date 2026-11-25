"""
Tests for the Stripe webhook dispatcher.

These bypass `stripe.Webhook.construct_event` by patching it — the
library's HMAC verification is third-party code we trust. What matters here
is our idempotency + bounded-retry logic and that the right handler is
invoked for each event type.
"""

import json
import re
from unittest import mock

from django.core import mail
from django.test import RequestFactory, override_settings

import pytest
import stripe

from apps.accounts.tests.recipes import make_user
from apps.base.tests import BaseTest
from apps.base.tests.mail import record_queued_emails, use_failing_mail_server
from apps.billing.constants import WEBHOOK_MAX_FAILURES, SubscriptionStatus
from apps.billing.models import WebhookEvent
from apps.billing.tests.recipes import BILLING_SETTINGS, make_customer, make_subscription
from apps.billing.webhooks import stripe_webhook
from apps.notifications.models import Notification
from apps.organizations.tests.recipes import make_org


def _post(event: dict):
    """Build a POST request that the webhook view will accept."""
    body = json.dumps(event).encode()
    return RequestFactory().post(
        "/webhooks/stripe/",
        data=body,
        content_type="application/json",
        headers={"stripe-signature": "t=0,v1=fake"},
    )


def _deliver(event: dict):
    """Deliver `event` to the webhook view, with `stripe.Webhook.construct_event` a pass-through that returns it."""
    with mock.patch("stripe.Webhook.construct_event", return_value=event):
        return stripe_webhook(_post(event))


@override_settings(**BILLING_SETTINGS)
class TestWebhookIdempotency(BaseTest):
    def test_replay_returns_200_without_reprocessing(self):
        customer = make_customer(make_org())
        event = {
            "id": "evt_replay",
            "type": "customer.subscription.updated",
            "data": {"object": {"id": "sub_x", "customer": customer.stripe_customer_id}},
        }

        # First delivery — handler runs, marker stored.
        first = _deliver(event)
        assert first.status_code == 200
        marker = WebhookEvent.objects.get(stripe_event_id="evt_replay")
        first_processed_at = marker.processed_at
        assert first_processed_at is not None

        # Second delivery — should short-circuit on IntegrityError + processed_at.
        second = _deliver(event)
        assert second.status_code == 200
        marker.refresh_from_db()
        # processed_at unchanged proves we didn't re-run the handler path.
        assert marker.processed_at == first_processed_at

    def test_unknown_event_type_marks_processed(self):
        event = {"id": "evt_unknown", "type": "totally.made.up", "data": {"object": {}}}

        response = _deliver(event)
        assert response.status_code == 200
        marker = WebhookEvent.objects.get(stripe_event_id="evt_unknown")
        assert marker.processed_at is not None
        assert marker.failure_count == 0

    def test_invalid_signature_returns_400(self):
        def _raise(payload, sig_header, secret):
            raise stripe.error.SignatureVerificationError("nope", sig_header)

        with mock.patch("stripe.Webhook.construct_event", side_effect=_raise):
            response = stripe_webhook(_post({"id": "evt_bad"}))

        assert response.status_code == 400
        assert not WebhookEvent.objects.exists()


@override_settings(**BILLING_SETTINGS)
class TestWebhookBoundedRetry(BaseTest):
    # A customer.subscription.updated event whose handler raises (see setUp).
    event = {
        "id": "evt_fail",
        "type": "customer.subscription.updated",
        "data": {"object": {"id": "sub_y", "customer": "cus_y"}},
    }

    def setUp(self):
        self.enterContext(
            mock.patch("apps.billing.webhooks.sync_subscription_from_stripe", side_effect=RuntimeError("boom"))
        )

    def test_failure_bumps_count_and_returns_500(self):
        response = _deliver(self.event)
        assert response.status_code == 500
        marker = WebhookEvent.objects.get(stripe_event_id="evt_fail")
        assert marker.processed_at is None
        assert marker.failure_count == 1
        assert "boom" in marker.last_error

    def test_marker_persists_across_failures(self):
        for _ in range(3):
            _deliver(self.event)

        # One marker total — failures don't churn rows.
        assert WebhookEvent.objects.filter(stripe_event_id="evt_fail").count() == 1
        marker = WebhookEvent.objects.get(stripe_event_id="evt_fail")
        assert marker.failure_count == 3
        assert marker.processed_at is None

    def test_gives_up_after_max_failures(self):
        # Climb to MAX - 1 failures with 500 responses.
        for _ in range(WEBHOOK_MAX_FAILURES - 1):
            response = _deliver(self.event)
            assert response.status_code == 500

        # The MAX'th delivery still runs the handler (it raises), bumps the
        # counter to MAX, then returns 200 because we've hit the ceiling.
        response = _deliver(self.event)
        assert response.status_code == 200
        marker = WebhookEvent.objects.get(stripe_event_id="evt_fail")
        assert marker.failure_count == WEBHOOK_MAX_FAILURES

        # Any further delivery hits the IntegrityError + give-up branch and
        # never re-invokes the handler — counter must not advance.
        response = _deliver(self.event)
        assert response.status_code == 200
        marker.refresh_from_db()
        assert marker.failure_count == WEBHOOK_MAX_FAILURES


@override_settings(**BILLING_SETTINGS)
class TestEventHandlers(BaseTest):
    @classmethod
    def setUpTestData(cls):
        cls.owner = make_user("owner@example.com", first_name="Michael", last_name="Scott")
        cls.org = make_org(cls.owner, name="Acme")
        cls.customer = make_customer(cls.org)
        cls.subscription = make_subscription(cls.org, plan_key="pro", status=SubscriptionStatus.ACTIVE)

    @pytest.fixture(autouse=True)
    def _pytest_fixtures(self, monkeypatch, settings):
        self.monkeypatch = monkeypatch
        self.settings_fixture = settings  # never assign self.settings: TestCase.settings() is a method

    def test_subscription_deleted_marks_subscription_canceled(self):
        # Don't actually send emails or notify in this test — the handler imports
        # them lazily, so we patch the symbols at the point of use.
        self.enterContext(mock.patch("apps.notifications.services.notify", return_value=[]))
        self.enterContext(mock.patch("apps.base.utils.email.send_email", return_value=None))
        event = {
            "id": "evt_del",
            "type": "customer.subscription.deleted",
            "data": {"object": {"id": self.subscription.stripe_subscription_id}},
        }

        response = _deliver(event)
        assert response.status_code == 200

        self.subscription.refresh_from_db()
        assert self.subscription.status == SubscriptionStatus.CANCELED
        assert self.subscription.canceled_at is not None

    def test_payment_failed_email_ends_the_sentence_once(self):
        # A name that already ends in a period ("Inc.") used to get a second one.
        self.enterContext(mock.patch("apps.notifications.services.notify", return_value=[]))
        for org_name, period in [("Acme", "."), ("Acme Inc.", "")]:
            with self.subTest(org_name=org_name):
                mail.outbox.clear()
                self.org.name = org_name
                self.org.save()
                # Each case is its own event: a redelivered one would stop at the dedupe marker.
                event = {
                    "id": f"evt_failed_{org_name}",
                    "type": "invoice.payment_failed",
                    "data": {"object": {"customer": self.customer.stripe_customer_id, "amount_due": 1000}},
                }

                assert _deliver(event).status_code == 200

                [email] = mail.outbox
                html, _ = email.alternatives[0]
                assert (
                    f"We weren't able to process the latest payment for {org_name}{period}" in email.body.splitlines()
                )
                assert re.search(rf"<strong>{re.escape(org_name)}</strong>{re.escape(period)}\s*</p>", html)

    def _assert_a_redelivered_event_notifies_the_owner_once(self, event_type: str, event_object: dict):
        # Sending the email inline raised after notify(), so the webhook answered 500, Stripe redelivered the event,
        # and every delivery added another in-app notification.
        use_failing_mail_server(self.settings_fixture)
        queued = record_queued_emails(self.monkeypatch)
        event = {"id": "evt_outage", "type": event_type, "data": {"object": event_object}}

        # Stripe redelivers any event that doesn't get a 2xx.
        statuses = [_deliver(event).status_code for _ in range(2)]

        assert statuses == [200, 200]
        assert Notification.objects.filter(recipient=self.owner).count() == 1
        [message] = queued
        assert message["to"] == ["Michael Scott <owner@example.com>"]

    def test_a_redelivered_cancellation_notifies_the_owner_once(self):
        self._assert_a_redelivered_event_notifies_the_owner_once(
            "customer.subscription.deleted", {"id": self.subscription.stripe_subscription_id}
        )

    def test_a_redelivered_payment_failure_notifies_the_owner_once(self):
        self._assert_a_redelivered_event_notifies_the_owner_once(
            "invoice.payment_failed", {"customer": self.customer.stripe_customer_id, "amount_due": 1000}
        )
