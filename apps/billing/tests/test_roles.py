from unittest.mock import patch

from django.core.exceptions import PermissionDenied
from django.test import RequestFactory

import pytest
from ninja.errors import HttpError

from apps.accounts.recipes import make_user
from apps.base.tests import BaseTest
from apps.billing.api import create_checkout, create_portal, get_subscription
from apps.billing.schemas import CheckoutIn
from apps.organizations.recipes import make_member, make_org
from apps.organizations.roles import ROLE_PERMISSIONS, OrgPerm, OrgRole
from apps.organizations.session import MockedOrg


def _grant_members(*perms):
    """Give the member role exactly `perms` until the block ends."""
    return patch.dict(ROLE_PERMISSIONS, {OrgRole.MEMBER: frozenset(perms)})


class TestBillingRoutesCheckTheirPermission(BaseTest):
    """
    Give the member role one permission at a time: only manage_billing opens billing's routes.

    Billing's router is mounted only with BILLING_ENABLED, which test settings leave off, so its routes are called
    directly.
    """

    @classmethod
    def setUpTestData(cls):
        cls.org = make_org(name="Dunder Mifflin", slug="dunder-mifflin")
        make_member(
            cls.org, make_user("michael@example.com", first_name="Michael", last_name="Scott"), role=OrgRole.OWNER
        )
        cls.member = make_member(cls.org, make_user("dwight@example.com", first_name="Dwight", last_name="Schrute"))

    def _billing_request(self, method, path):
        request = getattr(RequestFactory(), method)(path)
        request.user = self.member
        request.org = MockedOrg(pk=self.org.pk, id=self.org.pk, name=self.org.name, slug=self.org.slug)
        return request

    def test_billing_needs_manage_billing(self):
        for granted in OrgPerm:
            with self.subTest(granted=granted), _grant_members(granted):
                request = self._billing_request("get", "/api/billing/subscription/")

                if granted == OrgPerm.MANAGE_BILLING:
                    get_subscription(request)
                else:
                    with pytest.raises(PermissionDenied):
                        get_subscription(request)

    def test_billing_checkout_needs_manage_billing(self):
        for granted in OrgPerm:
            with self.subTest(granted=granted), _grant_members(granted):
                request = self._billing_request("post", "/api/billing/checkout/")
                payload = CheckoutIn(plan_key="nonexistent", billing_cycle="monthly")

                if granted == OrgPerm.MANAGE_BILLING:
                    with pytest.raises(HttpError) as exc_info:
                        create_checkout(request, payload)
                    assert exc_info.value.status_code == 404
                else:
                    with pytest.raises(PermissionDenied):
                        create_checkout(request, payload)

    def test_billing_portal_needs_manage_billing(self):
        for granted in OrgPerm:
            with self.subTest(granted=granted), _grant_members(granted):
                request = self._billing_request("post", "/api/billing/portal/")

                if granted == OrgPerm.MANAGE_BILLING:
                    with pytest.raises(HttpError) as exc_info:
                        create_portal(request)
                    assert exc_info.value.status_code == 409
                else:
                    with pytest.raises(PermissionDenied):
                        create_portal(request)
