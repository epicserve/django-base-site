"""
Tests for billing's Celery tasks and signals.

The BILLING_ENABLED=False smoke tests matter because a task or signal that called into `_stripe()` with billing
disabled would crash at startup, and the signals would crash unrelated org/member mutations.
"""

from datetime import timedelta

from django.core import mail
from django.db.models.signals import post_delete, post_save
from django.test import override_settings
from django.utils import timezone

import pytest

from apps.accounts.recipes import make_user
from apps.base.tests import BaseTest
from apps.base.tests.mail import record_queued_emails, use_failing_mail_server
from apps.billing.constants import SubscriptionStatus
from apps.billing.recipes import BILLING_SETTINGS, make_subscription
from apps.billing.tasks import check_trials_ending, reconcile_subscriptions
from apps.notifications.models import Notification
from apps.organizations.models import Organization, OrganizationMember
from apps.organizations.recipes import make_member, make_org
from apps.organizations.roles import OrgRole


class TestTasksBillingDisabled:
    """Both tasks return before touching the database, so these need none."""

    def test_check_trials_ending_no_op(self, settings):
        settings.BILLING_ENABLED = False
        assert check_trials_ending() == 0

    def test_reconcile_subscriptions_no_op(self, settings):
        settings.BILLING_ENABLED = False
        assert reconcile_subscriptions() == 0


@override_settings(BILLING_ENABLED=False)
class TestSeatSyncSignalDisabled(BaseTest):
    @classmethod
    def setUpTestData(cls):
        cls.org = make_org()
        cls.user = make_user()

    @pytest.fixture(autouse=True)
    def _pytest_fixtures(self, monkeypatch):
        self.monkeypatch = monkeypatch

    def setUp(self):
        # BillingConfig.ready() connects billing's receivers only when billing is on at startup, which it isn't under
        # the test settings, so without this these tests would pass with no receiver to test. Connect them, as on a
        # server that started with billing on, and afterwards disconnect the ones that weren't connected before: a
        # rollback doesn't undo a signal connection. The import is here because importing the module connects them.
        from apps.billing.signals import _customer_email_sync, _seat_sync

        for signal, receiver, sender, dispatch_uid in [
            (post_save, _seat_sync, OrganizationMember, "billing.seat_sync_post_save"),
            (post_delete, _seat_sync, OrganizationMember, "billing.seat_sync_post_delete"),
            (post_save, _customer_email_sync, Organization, "billing.customer_email_sync"),
        ]:
            # `disconnect` says whether it was connected; connecting it again keeps it.
            was_connected = signal.disconnect(receiver, sender=sender, dispatch_uid=dispatch_uid)
            signal.connect(receiver, sender=sender, dispatch_uid=dispatch_uid)
            if not was_connected:
                self.addCleanup(signal.disconnect, receiver, sender=sender, dispatch_uid=dispatch_uid)

    def test_member_save_does_not_call_stripe(self):
        """
        Post_save must not enqueue a seat-sync when billing is disabled.

        Proven by the absence of any on-commit callback, and so of any `sync_seat_quantity_by_id` call, during a
        normal OrganizationMember create.
        """
        called = []
        self.monkeypatch.setattr("apps.billing.services.sync_seat_quantity_by_id", called.append)

        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            make_member(self.org, self.user)

        assert callbacks == []
        assert called == []

    def test_org_save_does_not_call_stripe(self):
        called = []
        self.monkeypatch.setattr("apps.billing.services.sync_customer_email_by_id", called.append)

        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            self.org.billing_email = "billing@example.com"
            self.org.save()

        assert callbacks == []
        assert called == []


def _org_with_owner(name: str):
    """Make organization `name`, owned by "`name` Owner <owner@`name`.example>"."""
    owner = make_user(f"owner@{name.lower()}.example", first_name=name, last_name="Owner")
    return make_org(owner, name=name, slug=name.lower())


@override_settings(**BILLING_SETTINGS)
class TestCheckTrialsEnding(BaseTest):
    """
    The reminder goes out once, to the members who can manage billing, for a trial ending 2.5 to 3.5 days from now.

    The task runs daily, so the one-day window catches each trial on exactly one run.
    """

    @classmethod
    def setUpTestData(cls):
        cls.acme = _org_with_owner("Acme")

    @pytest.fixture(autouse=True)
    def _pytest_fixtures(self, monkeypatch, settings):
        self.monkeypatch = monkeypatch
        self.settings_fixture = settings  # never assign self.settings: TestCase.settings() is a method

    def _emailed(self):
        return sorted(address for message in mail.outbox for address in message.to)

    def test_reminds_a_trial_ending_in_the_window(self):
        # The task reads the clock a moment after the test does, so each edge case is a minute clear of the edge. A
        # trial is one-to-one with its organization, so each case has its own.
        cases = [
            ("Early", timedelta(days=2, hours=11, minutes=59), False),
            ("Opening", timedelta(days=2, hours=12, minutes=1), True),
            ("Middle", timedelta(days=3), True),
            ("Closing", timedelta(days=3, hours=11, minutes=59), True),
            ("Late", timedelta(days=3, hours=12, minutes=1), False),
        ]
        for name, ends_in, reminded in cases:
            with self.subTest(ends_in=ends_in):
                mail.outbox.clear()
                notifications_before = Notification.objects.count()
                subscription = make_subscription(_org_with_owner(name), trial_ends_in=ends_in)

                assert check_trials_ending() == int(reminded)

                subscription.refresh_from_db()
                assert (subscription.trial_ending_notified_at is not None) is reminded
                assert self._emailed() == ([f"{name} Owner <owner@{name.lower()}.example>"] if reminded else [])
                assert Notification.objects.count() - notifications_before == int(reminded)

    def test_reminds_once(self):
        make_subscription(self.acme, trial_ends_in=timedelta(days=3))

        assert (check_trials_ending(), check_trials_ending()) == (1, 0)

        assert len(mail.outbox) == 1
        assert Notification.objects.count() == 1

    def test_skips_a_trial_already_reminded(self):
        make_subscription(
            self.acme, trial_ends_in=timedelta(days=3), trial_ending_notified_at=timezone.now() - timedelta(hours=1)
        )

        assert check_trials_ending() == 0

        assert mail.outbox == []

    def test_skips_a_subscription_that_isnt_trialing(self):
        for status in SubscriptionStatus:
            if status == SubscriptionStatus.TRIALING:
                continue
            with self.subTest(status=status):
                make_subscription(make_org(make_user()), trial_ends_in=timedelta(days=3), status=status)

                assert check_trials_ending() == 0

                assert mail.outbox == []

    def test_only_members_who_manage_billing_hear_about_it(self):
        make_subscription(self.acme, trial_ends_in=timedelta(days=3))
        make_member(self.acme, make_user("member@acme.example"), role=OrgRole.MEMBER)

        assert check_trials_ending() == 1

        assert self._emailed() == ["Acme Owner <owner@acme.example>"]
        assert list(Notification.objects.values_list("recipient__email", flat=True)) == ["owner@acme.example"]

    def test_a_failed_email_doesnt_end_the_run(self):
        # Sending inline, the first failed email raised out of the loop, so every later trial in the run (and that
        # one's email) never got its reminder: the next day's run is outside the reminder window.
        use_failing_mail_server(self.settings_fixture)
        queued = record_queued_emails(self.monkeypatch)
        subscriptions = [
            make_subscription(self.acme, trial_ends_in=timedelta(days=3)),
            make_subscription(_org_with_owner("Globex"), trial_ends_in=timedelta(days=3)),
        ]

        assert check_trials_ending() == 2

        for subscription in subscriptions:
            subscription.refresh_from_db()
            assert subscription.trial_ending_notified_at is not None
        assert sorted(message["to"][0] for message in queued) == [
            "Acme Owner <owner@acme.example>",
            "Globex Owner <owner@globex.example>",
        ]
