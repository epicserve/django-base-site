"""
Tests for billing's Celery tasks and signals.

The BILLING_ENABLED=False smoke tests matter because a task or signal that called into `_stripe()` with billing
disabled would crash at startup, and the signals would crash unrelated org/member mutations.
"""

from datetime import timedelta

from django.utils import timezone

import pytest
from model_bakery import baker

from apps.base.tests.mail import record_queued_emails, use_failing_mail_server
from apps.billing.constants import SubscriptionStatus
from apps.billing.models import Subscription
from apps.billing.tasks import check_trials_ending, reconcile_subscriptions
from apps.notifications.models import Notification
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


@pytest.mark.django_db
class TestCheckTrialsEnding:
    """
    The reminder goes out once, to the members who can manage billing, for a trial ending 2.5 to 3.5 days from now.

    The task runs daily, so the one-day window catches each trial on exactly one run.
    """

    @pytest.fixture(autouse=True)
    def _setup(self, settings, mailoutbox):
        settings.BILLING_ENABLED = True
        settings.STRIPE_SECRET_KEY = "sk_test_dummy"  # noqa: S105
        self.outbox = mailoutbox
        self.now = timezone.now()

    def _trial(self, name, ends_in, status=SubscriptionStatus.TRIALING, notified_at=None):
        org = baker.make("organizations.Organization", name=name, slug=name.lower())
        owner = baker.make("accounts.User", first_name=name, last_name="Owner", email=f"owner@{name.lower()}.example")
        baker.make("organizations.OrganizationMember", organization=org, user=owner, role=OrgRole.OWNER)
        return Subscription.objects.create(
            organization=org,
            stripe_subscription_id=f"sub_{name.lower()}",
            plan_key="pro",
            status=status,
            trial_end=self.now + ends_in,
            trial_ending_notified_at=notified_at,
        )

    def _emailed(self):
        return sorted(address for message in self.outbox for address in message.to)

    # The task reads the clock a moment after the test does, so each edge case is a minute clear of the edge.
    @pytest.mark.parametrize(
        ("ends_in", "reminded"),
        [
            (timedelta(days=2, hours=11, minutes=59), False),
            (timedelta(days=2, hours=12, minutes=1), True),
            (timedelta(days=3), True),
            (timedelta(days=3, hours=11, minutes=59), True),
            (timedelta(days=3, hours=12, minutes=1), False),
        ],
    )
    def test_reminds_a_trial_ending_in_the_window(self, ends_in, reminded):
        subscription = self._trial("Acme", ends_in)

        assert check_trials_ending() == int(reminded)

        subscription.refresh_from_db()
        assert (subscription.trial_ending_notified_at is not None) is reminded
        assert self._emailed() == (["Acme Owner <owner@acme.example>"] if reminded else [])
        assert Notification.objects.count() == int(reminded)

    def test_reminds_once(self):
        self._trial("Acme", timedelta(days=3))

        assert (check_trials_ending(), check_trials_ending()) == (1, 0)

        assert len(self.outbox) == 1
        assert Notification.objects.count() == 1

    def test_skips_a_trial_already_reminded(self):
        self._trial("Acme", timedelta(days=3), notified_at=self.now - timedelta(hours=1))

        assert check_trials_ending() == 0

        assert self.outbox == []

    @pytest.mark.parametrize("status", [s for s in SubscriptionStatus if s != SubscriptionStatus.TRIALING])
    def test_skips_a_subscription_that_isnt_trialing(self, status):
        self._trial("Acme", timedelta(days=3), status=status)

        assert check_trials_ending() == 0

        assert self.outbox == []

    def test_only_members_who_manage_billing_hear_about_it(self):
        subscription = self._trial("Acme", timedelta(days=3))
        member = baker.make("accounts.User", email="member@acme.example")
        baker.make(
            "organizations.OrganizationMember", organization=subscription.organization, user=member, role=OrgRole.MEMBER
        )

        assert check_trials_ending() == 1

        assert self._emailed() == ["Acme Owner <owner@acme.example>"]
        assert list(Notification.objects.values_list("recipient__email", flat=True)) == ["owner@acme.example"]
