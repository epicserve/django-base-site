"""
An organization always keeps someone who holds each permission its roles grant.

Giving a role takes every permission it grants, so a permission nobody holds could never be given again. The API let an
owner demote themselves when they were the last owner, which left nobody who could manage the organization. The
Members tab disables Change Role on your own row, so only the API allowed it.
"""

import json

import pytest
from model_bakery import baker

from apps.accounts.models import User
from apps.organizations.models import Organization, OrganizationMember
from apps.organizations.roles import ROLE_PERMISSIONS, OrgPerm, OrgRole


@pytest.mark.django_db
class TestTheLastOwnerStays:
    @pytest.fixture(autouse=True)
    def _setup(self, client):
        self.org = baker.make(Organization, name="Dunder Mifflin", slug="dunder-mifflin")
        self.michael = self._member("michael@example.com", OrgRole.OWNER)
        self.client = client
        self.client.force_login(self.michael.user)
        session = self.client.session
        session["organization_data"] = json.dumps(
            {"pk": self.org.pk, "id": self.org.pk, "name": self.org.name, "slug": self.org.slug}
        )
        session.save()

    def _member(self, email, role):
        return baker.make(OrganizationMember, organization=self.org, user=baker.make(User, email=email), role=role)

    def _set_role(self, membership, role):
        return self.client.patch(
            f"/api/organization-members/{membership.pk}/",
            data=json.dumps({"role": role}),
            content_type="application/json",
        )

    def _roles(self):
        return dict(OrganizationMember.objects.values_list("user__email", "role"))

    def test_the_last_owner_cant_demote_themselves(self):
        self._member("dwight@example.com", OrgRole.MEMBER)

        response = self._set_role(self.michael, OrgRole.MEMBER)

        assert response.status_code == 400
        assert response.json() == {
            "detail": "Nobody else in the organization can manage the organization's settings. Give someone else the "
            "owner role first."
        }
        assert self._roles() == {"michael@example.com": OrgRole.OWNER, "dwight@example.com": OrgRole.MEMBER}

    def test_an_owner_can_step_down_while_another_owner_stays(self):
        jan = self._member("jan@example.com", OrgRole.OWNER)

        assert self._set_role(self.michael, OrgRole.MEMBER).status_code == 200

        assert self._roles() == {"michael@example.com": OrgRole.MEMBER, "jan@example.com": OrgRole.OWNER}
        assert jan.role == OrgRole.OWNER

    def test_demoting_the_other_owner_leaves_you_the_last(self):
        jan = self._member("jan@example.com", OrgRole.OWNER)

        demote_jan = self._set_role(jan, OrgRole.MEMBER)
        demote_self = self._set_role(self.michael, OrgRole.MEMBER)

        assert (demote_jan.status_code, demote_self.status_code) == (200, 400)
        assert self._roles() == {"michael@example.com": OrgRole.OWNER, "jan@example.com": OrgRole.MEMBER}

    def test_another_role_that_holds_only_some_permissions_isnt_enough(self, monkeypatch):
        # Stands in for an admin role a project might add. Admins couldn't make an owner, so billing would be lost.
        monkeypatch.setitem(ROLE_PERMISSIONS, OrgRole.MEMBER, frozenset({OrgPerm.MANAGE_MEMBERS, OrgPerm.MANAGE_TEAMS}))
        self._member("dwight@example.com", OrgRole.MEMBER)

        response = self._set_role(self.michael, OrgRole.MEMBER)

        assert response.status_code == 400
        assert "manage the organization's settings" in response.json()["detail"]
        assert self._roles()["michael@example.com"] == OrgRole.OWNER
