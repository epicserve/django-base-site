"""
Smoke tests for the BILLING_ENABLED=False short-circuit.

If these were to slip and call into `_stripe()` with billing disabled, the
tasks would crash at startup and signals would crash unrelated org/member
mutations.
"""

import pytest
from model_bakery import baker

from apps.billing.tasks import check_trials_ending, reconcile_subscriptions


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
