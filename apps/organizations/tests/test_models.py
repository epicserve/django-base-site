import pytest
from model_bakery import baker

from apps.accounts.models import User


@pytest.mark.django_db
class TestOrganizationMembershipProperties:
    """
    Regression coverage for the members / regular_members / owners properties.

    Previously these filtered `User.pk__in=organizationmember_set.values_list("pk", ...)`
    — i.e. User pks against OrganizationMember pks. They now filter on `user_id`.
    """

    def test_owners_returns_owning_users(self):
        org = baker.make("organizations.Organization")
        owner = baker.make("accounts.User")
        regular = baker.make("accounts.User")
        baker.make("organizations.OrganizationMember", organization=org, user=owner, is_owner=True)
        baker.make("organizations.OrganizationMember", organization=org, user=regular, is_owner=False)

        owners = list(org.owners)
        assert owners == [owner]

    def test_members_returns_all_users(self):
        org = baker.make("organizations.Organization")
        owner = baker.make("accounts.User")
        regular = baker.make("accounts.User")
        baker.make("organizations.OrganizationMember", organization=org, user=owner, is_owner=True)
        baker.make("organizations.OrganizationMember", organization=org, user=regular, is_owner=False)

        assert set(org.members) == {owner, regular}

    def test_regular_members_excludes_owners(self):
        org = baker.make("organizations.Organization")
        owner = baker.make("accounts.User")
        regular = baker.make("accounts.User")
        baker.make("organizations.OrganizationMember", organization=org, user=owner, is_owner=True)
        baker.make("organizations.OrganizationMember", organization=org, user=regular, is_owner=False)

        assert list(org.regular_members) == [regular]

    def test_owners_does_not_leak_across_orgs(self):
        """
        Build a deliberate pk skew and confirm the property still resolves.

        Insert extra users so user pks and member pks diverge — under the old
        buggy join this test would fail because the wrong rows would match.
        """
        baker.make("accounts.User", _quantity=3)
        org_a = baker.make("organizations.Organization")
        org_b = baker.make("organizations.Organization")
        user_a = baker.make("accounts.User")
        user_b = baker.make("accounts.User")
        baker.make("organizations.OrganizationMember", organization=org_a, user=user_a, is_owner=True)
        baker.make("organizations.OrganizationMember", organization=org_b, user=user_b, is_owner=True)

        assert list(org_a.owners) == [user_a]
        assert list(org_b.owners) == [user_b]
        # And the cross-pollution check: org_a.owners shouldn't contain User
        # rows whose pk happens to match an OrganizationMember pk.
        assert user_b not in list(org_a.owners)
        assert User.objects.filter(pk__in=[user_a.pk, user_b.pk]).count() == 2
