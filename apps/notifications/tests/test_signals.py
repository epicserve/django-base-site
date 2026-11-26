from django.db.models.signals import post_delete
from django.test import override_settings

from apps.accounts.recipes import make_user
from apps.base.tests import BaseTest
from apps.notifications.models import Notification
from apps.notifications.services import notify
from apps.notifications.signals import _delete_notifications_for_target, connect_target_receivers
from apps.organizations.models import Organization
from apps.organizations.recipes import make_org


# Use a model that already exists in the project (Organization) as a stand-in target so we don't need a fixture model.
@override_settings(NOTIFICATIONS_TARGET_MODELS=["organizations.Organization"])
class TestTargetDeleteCascade(BaseTest):
    """
    Pin the GenericForeignKey post_delete cascade contract.

    Notification.target is a GenericForeignKey — the database has no FK CASCADE.
    `connect_target_receivers()` wires a per-model post_delete signal so deleting
    the target row cleans up its notifications. If the wiring or the signal
    handler regresses, this test fails before notifications leak in production.

    The notifications aren't scoped to the target organization: `Notification.organization` is a real foreign key, so
    deleting that organization would delete them with or without the receiver.
    """

    @classmethod
    def setUpTestData(cls):
        cls.alice = make_user()
        cls.target = make_org()

    def setUp(self):
        # A rollback doesn't undo a signal connection, so connect the receiver for each test and disconnect it after,
        # so it doesn't leak into the rest of the suite.
        connect_target_receivers()
        self.addCleanup(
            post_delete.disconnect,
            _delete_notifications_for_target,
            sender=Organization,
            dispatch_uid="notifications.cascade.organizations.Organization",
        )

    def test_target_delete_cleans_up_notifications(self):
        notify([self.alice], title="about the org", target=self.target)
        assert Notification.objects.count() == 1
        self.target.delete()
        assert Notification.objects.count() == 0

    def test_unrelated_target_delete_leaves_notifications_alone(self):
        other_target = make_org()
        notify([self.alice], title="about target", target=self.target)
        other_target.delete()
        assert Notification.objects.count() == 1
