import pytest
from model_bakery import baker

from apps.accounts.models import User
from apps.organizations.roles import OrgPerm, OrgRole


@pytest.mark.django_db
class TestOrganizationMembershipProperties:
    """
    Regression coverage for `members` and `members_with_perm`.

    These once filtered `User.pk__in=organizationmember_set.values_list("pk", ...)`, i.e. User pks against
    OrganizationMember pks. They filter on `user_id`.
    """

    def test_members_with_perm_returns_the_users_whose_role_grants_it(self):
        org = baker.make("organizations.Organization")
        owner = baker.make("accounts.User")
        member = baker.make("accounts.User")
        baker.make("organizations.OrganizationMember", organization=org, user=owner, role=OrgRole.OWNER)
        baker.make("organizations.OrganizationMember", organization=org, user=member, role=OrgRole.MEMBER)

        assert list(org.members_with_perm(OrgPerm.MANAGE_BILLING)) == [owner]

    def test_members_returns_all_users(self):
        org = baker.make("organizations.Organization")
        owner = baker.make("accounts.User")
        member = baker.make("accounts.User")
        baker.make("organizations.OrganizationMember", organization=org, user=owner, role=OrgRole.OWNER)
        baker.make("organizations.OrganizationMember", organization=org, user=member, role=OrgRole.MEMBER)

        assert set(org.members) == {owner, member}

    def test_members_with_perm_does_not_leak_across_orgs(self):
        """
        Build a deliberate pk skew and confirm the query still resolves.

        Insert extra users so user pks and member pks diverge: joining on the wrong column would match the wrong rows.
        """
        baker.make("accounts.User", _quantity=3)
        org_a = baker.make("organizations.Organization")
        org_b = baker.make("organizations.Organization")
        user_a = baker.make("accounts.User")
        user_b = baker.make("accounts.User")
        baker.make("organizations.OrganizationMember", organization=org_a, user=user_a, role=OrgRole.OWNER)
        baker.make("organizations.OrganizationMember", organization=org_b, user=user_b, role=OrgRole.OWNER)

        assert list(org_a.members_with_perm(OrgPerm.MANAGE_BILLING)) == [user_a]
        assert list(org_b.members_with_perm(OrgPerm.MANAGE_BILLING)) == [user_b]
        assert User.objects.filter(pk__in=[user_a.pk, user_b.pk]).count() == 2
