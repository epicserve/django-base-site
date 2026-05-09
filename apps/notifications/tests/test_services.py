from datetime import timedelta

from django.utils import timezone

import pytest
from model_bakery import baker

from apps.accounts.models import User
from apps.notifications.constants import NotificationChannel
from apps.notifications.models import Notification, NotificationPreference
from apps.notifications.services import notify
from apps.notifications.tasks import purge_expired
from apps.organizations.models import OrganizationMember

COMMENTS_CATEGORY = {
    "key": "comments",
    "label": "Comments",
    "default_channels": (NotificationChannel.IN_APP,),
}


@pytest.mark.django_db
class TestNotify:
    @pytest.fixture(autouse=True)
    def _setup(self, db):
        self.alice = User.objects.create_user(username="alice", password="secret")  # noqa: S106
        self.bob = User.objects.create_user(username="bob", password="secret")  # noqa: S106

    def test_creates_one_row_per_recipient(self):
        notify([self.alice, self.bob], title="hi")
        assert Notification.objects.count() == 2

    def test_persists_category_and_expires_at(self):
        when = timezone.now() + timedelta(days=1)
        notify([self.alice], title="hi", category="comments", expires_at=when)
        n = Notification.objects.get()
        assert n.category == "comments"
        assert n.expires_at is not None

    def test_skips_recipients_with_in_app_disabled(self, settings):
        settings.NOTIFICATIONS_CATEGORIES = [COMMENTS_CATEGORY]
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
        org = baker.make("organizations.Organization")
        OrganizationMember.objects.create(organization=org, user=self.alice)
        # bob is not a member of `org` — notify() must refuse to create the row.
        with pytest.raises(ValueError, match="not members of organization"):
            notify([self.alice, self.bob], title="hi", organization=org)
        assert Notification.objects.count() == 0

    def test_allows_org_recipients_when_all_are_members(self):
        org = baker.make("organizations.Organization")
        OrganizationMember.objects.create(organization=org, user=self.alice)
        OrganizationMember.objects.create(organization=org, user=self.bob)
        notify([self.alice, self.bob], title="hi", organization=org)
        assert Notification.objects.count() == 2


@pytest.mark.django_db
class TestPurgeExpired:
    @pytest.fixture(autouse=True)
    def _setup(self, db):
        self.alice = User.objects.create_user(username="alice", password="secret")  # noqa: S106

    def test_deletes_rows_past_expires_at(self):
        notify([self.alice], title="expired", expires_at=timezone.now() - timedelta(seconds=1))
        notify([self.alice], title="future", expires_at=timezone.now() + timedelta(days=1))
        deleted = purge_expired()
        assert deleted == 1
        assert Notification.objects.get().title == "future"

    def test_deletes_rows_older_than_retention_default(self):
        notify([self.alice], title="old")
        Notification.objects.update(created=timezone.now() - timedelta(days=120))
        notify([self.alice], title="recent")

        deleted = purge_expired()
        assert deleted == 1
        assert Notification.objects.get().title == "recent"

    def test_days_zero_purges_everything(self):
        notify([self.alice], title="hi")
        deleted = purge_expired(days=0)
        assert deleted == 1
