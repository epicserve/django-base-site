"""
One user's invites are capped per hour and per day. Before, `create_invite` had no limit.

Inviting someone emails whatever address the sender typed, and anyone can sign up and create an organization.
"""

import json
from itertools import count

from django.core.cache import cache
from django.test import Client

import pytest
from model_bakery import baker

from apps.accounts.models import User
from apps.organizations.api import INVITE_THROTTLES
from apps.organizations.models import Organization, OrganizationInvite, OrganizationMember
from apps.organizations.roles import OrgRole

HOUR = 60 * 60


@pytest.mark.django_db
class TestInviteThrottle:
    @pytest.fixture(autouse=True)
    def _setup(self, client, settings, monkeypatch):
        # Test settings use a dummy cache, which remembers nothing, so nothing would ever be throttled.
        settings.CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
        cache.clear()
        self.now = 1_000_000.0
        for throttle in INVITE_THROTTLES:
            monkeypatch.setattr(throttle, "timer", lambda: self.now)
        self.addresses = (f"guest{n}@example.com" for n in count())
        self.client = client
        self.michael = self._owner(client, "michael@example.com")

    def _owner(self, client, email):
        user = baker.make(User, email=email)
        org = baker.make(Organization, slug=email.split("@")[0])
        baker.make(OrganizationMember, organization=org, user=user, role=OrgRole.OWNER)
        client.force_login(user)
        session = client.session
        session["organization_data"] = json.dumps({"pk": org.pk, "id": org.pk, "name": org.name, "slug": org.slug})
        session.save()
        return user

    def _invite(self, client=None):
        return (client or self.client).post(
            "/api/organization-invites/",
            data=json.dumps({"invitee_email": next(self.addresses)}),
            content_type="application/json",
        )

    def _invite_many(self, n):
        return [self._invite().status_code for _ in range(n)]

    def test_30_invites_an_hour_then_429(self):
        assert self._invite_many(30) == [201] * 30

        response = self._invite()

        assert response.status_code == 429
        assert response.json() == {"detail": "Too many requests."}
        assert int(response["Retry-After"]) > 0
        assert OrganizationInvite.objects.count() == 30

    def test_the_hourly_limit_resets_after_an_hour(self):
        self._invite_many(30)
        self.now += HOUR + 1

        assert self._invite().status_code == 201

    def test_100_invites_a_day(self):
        sent = []
        for batch in (30, 30, 30, 10):
            sent += self._invite_many(batch)
            self.now += HOUR + 1

        assert sent == [201] * 100
        assert self._invite().status_code == 429

        self.now += 24 * HOUR

        assert self._invite().status_code == 201

    def test_each_user_has_their_own_limit(self):
        self._invite_many(30)
        jan_client = Client()
        self._owner(jan_client, "jan@example.com")

        assert self._invite().status_code == 429
        assert self._invite(jan_client).status_code == 201
