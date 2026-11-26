from django.core.exceptions import ValidationError

import pytest

from apps.accounts.models import User
from apps.accounts.recipes import make_user
from apps.base.tests import BaseTest
from apps.organizations.models import OrganizationInvite
from apps.organizations.recipes import make_invite, make_member, make_org
from apps.organizations.roles import OrgPerm, OrgRole


class TestOrganizationMembershipProperties(BaseTest):
    """
    Regression coverage for `members` and `members_with_perm`.

    These once filtered `User.pk__in=organizationmember_set.values_list("pk", ...)`, i.e. User pks against
    OrganizationMember pks. They filter on `user_id`.
    """

    @classmethod
    def setUpTestData(cls):
        # Extra users first, so user pks and member pks diverge: joining on the wrong column would match the wrong rows.
        for _ in range(3):
            make_user()
        cls.owner = make_user()
        cls.member = make_user()
        cls.org = make_org(cls.owner)
        make_member(cls.org, cls.member)
        cls.other_owner = make_user()
        cls.other_org = make_org(cls.other_owner)

    def test_members_with_perm_returns_the_users_whose_role_grants_it(self):
        assert list(self.org.members_with_perm(OrgPerm.MANAGE_BILLING)) == [self.owner]

    def test_members_returns_all_users(self):
        assert set(self.org.members) == {self.owner, self.member}

    def test_members_with_perm_does_not_leak_across_orgs(self):
        assert list(self.org.members_with_perm(OrgPerm.MANAGE_BILLING)) == [self.owner]
        assert list(self.other_org.members_with_perm(OrgPerm.MANAGE_BILLING)) == [self.other_owner]
        assert User.objects.filter(pk__in=[self.owner.pk, self.other_owner.pk]).count() == 2


class TestOrganizationInvite(BaseTest):
    @classmethod
    def setUpTestData(cls):
        cls.owner = make_user()
        cls.org = make_org(cls.owner)

    def test_save_makes_a_key(self):
        invite = make_invite(self.org, self.owner)

        assert len(invite.key) == 32
        assert make_invite(self.org, self.owner).key != invite.key

    def test_save_keeps_a_key_it_was_given(self):
        invite = OrganizationInvite(
            organization=self.org, sender=self.owner, invitee_email="jim@example.com", key="k" * 32
        )

        invite.save()

        invite.refresh_from_db()
        assert invite.key == "k" * 32

    def test_saving_an_invite_again_is_not_a_duplicate_of_itself(self):
        invite = make_invite(self.org, self.owner, email="jim@example.com")

        invite.role = OrgRole.OWNER
        invite.save()

        invite.refresh_from_db()
        assert invite.role == OrgRole.OWNER

    def test_a_second_invite_for_the_same_email_is_still_refused(self):
        make_invite(self.org, self.owner, email="jim@example.com")

        with pytest.raises(ValidationError):
            make_invite(self.org, self.owner, email="jim@example.com")
