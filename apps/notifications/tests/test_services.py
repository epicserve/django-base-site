from datetime import timedelta

from django.test import override_settings
from django.utils import timezone

import pytest

from apps.accounts.tests.recipes import make_user
from apps.base.tests import BaseTest
from apps.notifications.models import Notification, NotificationPreference
from apps.notifications.services import notify
from apps.notifications.tasks import purge_expired
from apps.notifications.tests.recipes import COMMENTS_CATEGORY, make_notification
from apps.organizations.tests.recipes import make_member, make_org


class TestNotify(BaseTest):
    @classmethod
    def setUpTestData(cls):
        cls.alice = make_user("alice@example.com")
        cls.bob = make_user("bob@example.com")
        # Alice is a member and Bob isn't, until a test adds him.
        cls.org = make_org(cls.alice)

    def test_creates_one_row_per_recipient(self):
        notify([self.alice, self.bob], title="hi")
        assert Notification.objects.count() == 2

    def test_persists_category_and_expires_at(self):
        when = timezone.now() + timedelta(days=1)
        notify([self.alice], title="hi", category="comments", expires_at=when)
        n = Notification.objects.get()
        assert n.category == "comments"
        assert n.expires_at is not None

    @override_settings(NOTIFICATIONS_CATEGORIES=[COMMENTS_CATEGORY])
    def test_skips_recipients_with_in_app_disabled(self):
        # Bob has no preference row, so he gets the category's default channels, in-app among them.
        NotificationPreference.objects.create(user=self.alice, category="comments", in_app=False)
        notify([self.alice, self.bob], title="hi", category="comments")
        assert Notification.objects.filter(recipient=self.alice).count() == 0
        assert Notification.objects.filter(recipient=self.bob).count() == 1

    def test_unregistered_category_always_sends(self):
        # Defensive: a category nobody registered shouldn't silently drop.
        NotificationPreference.objects.create(user=self.alice, category="orphan", in_app=False)
        notify([self.alice], title="hi", category="orphan")
        assert Notification.objects.count() == 1

    def test_raises_when_recipient_not_in_org(self):
        # bob is not a member of `org` — notify() must refuse to create the row.
        with pytest.raises(ValueError, match="not members of organization"):
            notify([self.alice, self.bob], title="hi", organization=self.org)
        assert Notification.objects.count() == 0

    def test_allows_org_recipients_when_all_are_members(self):
        make_member(self.org, self.bob)
        notify([self.alice, self.bob], title="hi", organization=self.org)
        assert Notification.objects.count() == 2


class TestPurgeExpired(BaseTest):
    @classmethod
    def setUpTestData(cls):
        cls.alice = make_user("alice@example.com")

    def test_deletes_rows_past_expires_at(self):
        make_notification(self.alice, title="expired", expires_at=timezone.now() - timedelta(seconds=1))
        make_notification(self.alice, title="future", expires_at=timezone.now() + timedelta(days=1))
        deleted = purge_expired()
        assert deleted == 1
        assert Notification.objects.get().title == "future"

    def test_deletes_rows_older_than_retention_default(self):
        make_notification(self.alice, title="old")
        Notification.objects.update(created=timezone.now() - timedelta(days=120))
        make_notification(self.alice, title="recent")

        deleted = purge_expired()
        assert deleted == 1
        assert Notification.objects.get().title == "recent"

    def test_days_zero_purges_everything(self):
        make_notification(self.alice, title="hi")
        deleted = purge_expired(days=0)
        assert deleted == 1
