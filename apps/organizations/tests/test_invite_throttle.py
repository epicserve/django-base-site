"""
One user's invites are capped per hour and per day. Before, `create_invite` had no limit.

Inviting someone emails whatever address the sender typed, and anyone can sign up and create an organization.
"""

import json
from itertools import count
from unittest.mock import patch

from django.core.cache import cache
from django.test import Client, override_settings

from apps.accounts.tests.recipes import make_user
from apps.base.tests import BaseTest
from apps.base.tests.sign_in import sign_in
from apps.organizations.api import INVITE_THROTTLES
from apps.organizations.models import OrganizationInvite
from apps.organizations.tests.recipes import make_org

HOUR = 60 * 60


# Test settings use a dummy cache, which remembers nothing, so nothing would ever be throttled.
@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
class TestInviteThrottle(BaseTest):
    @classmethod
    def setUpTestData(cls):
        cls.michael = make_user("michael@example.com")
        cls.org = make_org(cls.michael)

    def setUp(self):
        # The cache isn't rolled back, and michael keeps his pk from test to test, so his counts would carry over.
        cache.clear()
        self.addCleanup(cache.clear)
        self.now = 1_000_000.0
        for throttle in INVITE_THROTTLES:
            self.enterContext(patch.object(throttle, "timer", lambda: self.now))
        self.addresses = (f"guest{n}@example.com" for n in count())
        sign_in(self.client, self.michael, self.org)

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
        jan = make_user("jan@example.com")
        jan_client = sign_in(Client(), jan, make_org(jan))

        assert self._invite().status_code == 429
        assert self._invite(jan_client).status_code == 201
