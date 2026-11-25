"""
An organization always keeps someone who holds each permission its roles grant.

Giving a role takes every permission it grants, so a permission nobody holds could never be given again. The API let an
owner demote themselves when they were the last owner, which left nobody who could manage the organization. The
Members tab disables Change Role on your own row, so only the API allowed it.
"""

import json
from unittest.mock import patch

from apps.accounts.tests.recipes import make_user
from apps.base.tests import BaseTest
from apps.base.tests.sign_in import sign_in
from apps.organizations.models import OrganizationMember
from apps.organizations.roles import ROLE_PERMISSIONS, OrgPerm, OrgRole
from apps.organizations.tests.recipes import make_member, make_org


def _membership(org, email, role):
    user = make_member(org, make_user(email), role=role)
    return OrganizationMember.objects.get(organization=org, user=user)


class TestTheLastOwnerStays(BaseTest):
    @classmethod
    def setUpTestData(cls):
        cls.org = make_org(name="Dunder Mifflin", slug="dunder-mifflin")
        cls.michael = _membership(cls.org, "michael@example.com", OrgRole.OWNER)

    def setUp(self):
        sign_in(self.client, self.michael.user, self.org)

    def _set_role(self, membership, role):
        return self.client.patch(
            f"/api/organization-members/{membership.pk}/",
            data=json.dumps({"role": role}),
            content_type="application/json",
        )

    def _roles(self):
        return dict(OrganizationMember.objects.values_list("user__email", "role"))

    def test_the_last_owner_cant_demote_themselves(self):
        _membership(self.org, "dwight@example.com", OrgRole.MEMBER)

        response = self._set_role(self.michael, OrgRole.MEMBER)

        assert response.status_code == 400
        assert response.json() == {
            "detail": "Nobody else in the organization can manage the organization's settings. Give someone else the "
            "owner role first."
        }
        assert self._roles() == {"michael@example.com": OrgRole.OWNER, "dwight@example.com": OrgRole.MEMBER}

    def test_an_owner_can_step_down_while_another_owner_stays(self):
        jan = _membership(self.org, "jan@example.com", OrgRole.OWNER)

        assert self._set_role(self.michael, OrgRole.MEMBER).status_code == 200

        assert self._roles() == {"michael@example.com": OrgRole.MEMBER, "jan@example.com": OrgRole.OWNER}
        assert jan.role == OrgRole.OWNER

    def test_demoting_the_other_owner_leaves_you_the_last(self):
        jan = _membership(self.org, "jan@example.com", OrgRole.OWNER)

        demote_jan = self._set_role(jan, OrgRole.MEMBER)
        demote_self = self._set_role(self.michael, OrgRole.MEMBER)

        assert (demote_jan.status_code, demote_self.status_code) == (200, 400)
        assert self._roles() == {"michael@example.com": OrgRole.OWNER, "jan@example.com": OrgRole.MEMBER}

    def test_another_role_that_holds_only_some_permissions_isnt_enough(self):
        # Stands in for an admin role a project might add. Admins couldn't make an owner, so billing would be lost.
        _membership(self.org, "dwight@example.com", OrgRole.MEMBER)

        with patch.dict(ROLE_PERMISSIONS, {OrgRole.MEMBER: frozenset({OrgPerm.MANAGE_MEMBERS, OrgPerm.MANAGE_TEAMS})}):
            response = self._set_role(self.michael, OrgRole.MEMBER)

        assert response.status_code == 400
        assert "manage the organization's settings" in response.json()["detail"]
        assert self._roles()["michael@example.com"] == OrgRole.OWNER
