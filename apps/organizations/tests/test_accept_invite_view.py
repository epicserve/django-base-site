import pytest
from allauth.account.models import EmailAddress
from model_bakery import baker

from apps.accounts.models import User
from apps.organizations.models import Organization, OrganizationInvite, OrganizationMember


@pytest.fixture()
def inviter(db):
    user = baker.make(User, email="michael.scott@dundermifflin.com")
    user.set_password("dundermifflin")
    user.save()
    EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)
    return user


@pytest.fixture()
def invite(inviter):
    organization = baker.make(Organization, name="Dunder Mifflin", slug="dunder-mifflin")
    OrganizationMember.objects.create(organization=organization, user=inviter, is_owner=True)
    return OrganizationInvite.objects.create(
        organization=organization,
        sender=inviter,
        invitee_email="pam.beesly@dundermifflin.com",
    )


@pytest.mark.django_db
def test_authenticated_user_can_load_invite_accept_page(client, settings, inviter, invite):
    """
    Regression test for the invite accept page for authenticated users.

    The SPA migration dropped the `organizations` namespace but
    `layouts/base.html` still referenced `{% url 'organizations:...' %}` tags
    in the authenticated-user nav, so any logged-in user hitting the invite
    accept page got a NoReverseMatch.
    """
    # VITE_DEV_MODE=True skips the production manifest lookup for vite_asset
    # tags so template rendering succeeds without a built frontend.
    settings.VITE_DEV_MODE = True
    client.force_login(inviter)

    response = client.get(invite.accept_invite_url)

    # 200 (not NoReverseMatch/500) is the core regression assertion. Inviter
    # is a member of the org, so the template renders the "Already a Member"
    # branch rather than the join form.
    assert response.status_code == 200
    assert b"Already a Member" in response.content
