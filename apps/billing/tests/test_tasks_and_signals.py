"""
Smoke tests for the BILLING_ENABLED=False short-circuit.

If these were to slip and call into `_stripe()` with billing disabled, the
tasks would crash at startup and signals would crash unrelated org/member
mutations.
"""

from datetime import timedelta

from django.utils import timezone

import pytest
from model_bakery import baker

from apps.base.tests.mail import record_queued_emails, use_failing_mail_server
from apps.billing.constants import SubscriptionStatus
from apps.billing.models import Subscription
from apps.billing.tasks import check_trials_ending, reconcile_subscriptions
from apps.organizations.roles import OrgRole


@pytest.mark.django_db
class TestTasksBillingDisabled:
    def test_check_trials_ending_no_op(self, settings):
        settings.BILLING_ENABLED = False
        assert check_trials_ending() == 0

    def test_reconcile_subscriptions_no_op(self, settings):
        settings.BILLING_ENABLED = False
        assert reconcile_subscriptions() == 0


@pytest.mark.django_db
class TestSeatSyncSignalDisabled:
    def test_member_save_does_not_call_stripe(self, settings, monkeypatch):
        """
        Post_save must not enqueue a seat-sync when billing is disabled.

        Proven by the absence of any `sync_seat_quantity_by_id` call during a
        normal OrganizationMember create.
        """
        settings.BILLING_ENABLED = False
        called = []
        monkeypatch.setattr(
            "apps.billing.services.sync_seat_quantity_by_id",
            lambda org_id: called.append(org_id),
        )

        org = baker.make("organizations.Organization")
        user = baker.make("accounts.User")
        baker.make("organizations.OrganizationMember", organization=org, user=user)

        assert called == []

    def test_org_save_does_not_call_stripe(self, settings, monkeypatch):
        settings.BILLING_ENABLED = False
        called = []
        monkeypatch.setattr(
            "apps.billing.services.sync_customer_email_by_id",
            lambda org_id: called.append(org_id),
        )

        org = baker.make("organizations.Organization")
        org.billing_email = "billing@example.com"
        org.save()

        assert called == []


@pytest.mark.django_db
class TestCheckTrialsEndingMailOutage:
    def test_a_failed_email_doesnt_end_the_run(self, settings, monkeypatch):
        # Sending inline, the first failed email raised out of the loop, so every later trial in the run (and that
        # one's email) never got its reminder: the next day's run is outside the reminder window.
        settings.BILLING_ENABLED = True
        settings.STRIPE_SECRET_KEY = "sk_test_dummy"  # noqa: S105
        use_failing_mail_server(settings)
        queued = record_queued_emails(monkeypatch)
        trial_end = timezone.now() + timedelta(days=3)
        subscriptions = []
        for name in ("Acme", "Globex"):
            org = baker.make("organizations.Organization", name=name)
            owner = baker.make(
                "accounts.User", first_name=name, last_name="Owner", email=f"owner@{name.lower()}.example"
            )
            baker.make("organizations.OrganizationMember", organization=org, user=owner, role=OrgRole.OWNER)
            subscriptions.append(
                Subscription.objects.create(
                    organization=org,
                    stripe_subscription_id=f"sub_{name.lower()}",
                    plan_key="pro",
                    status=SubscriptionStatus.TRIALING,
                    trial_end=trial_end,
                )
            )

        assert check_trials_ending() == 2

        for subscription in subscriptions:
            subscription.refresh_from_db()
            assert subscription.trial_ending_notified_at is not None
        assert sorted(message["to"][0] for message in queued) == [
            "Acme Owner <owner@acme.example>",
            "Globex Owner <owner@globex.example>",
        ]
