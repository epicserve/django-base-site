"""End-to-end tests for the organization invitation flow.

Covers the SPA-driven accept-invite page that the invitation email links to:

  /organizations/invite/<key>/accept/

The page is a Vue route served via SPAView; invite metadata loads from
/api/invite-by-key/<key>/, and accept/decline POST to the same prefix.
"""

import re

import pytest
from model_bakery import baker
from playwright.sync_api import Page, expect


@pytest.fixture()
def org(db, user):
    from apps.organizations.models import Organization, OrganizationMember

    org = Organization.objects.create(name="Dunder Mifflin", slug="dunder-mifflin")
    OrganizationMember.objects.create(organization=org, user=user, is_owner=True)
    return org


@pytest.fixture()
def invite(db, org, user):
    from apps.organizations.models import OrganizationInvite

    return OrganizationInvite.objects.create(
        organization=org,
        sender=user,
        invitee_email="jim.halpert@dundermifflin.com",
    )


@pytest.fixture()
def expired_invite(db, org, user):
    from datetime import timedelta

    from django.utils import timezone

    from apps.organizations.models import OrganizationInvite

    inv = OrganizationInvite.objects.create(
        organization=org,
        sender=user,
        invitee_email="pam.beesly@dundermifflin.com",
    )
    OrganizationInvite.objects.filter(pk=inv.pk).update(
        created=timezone.now() - timedelta(days=inv.expired_in_days + 1)
    )
    inv.refresh_from_db()
    return inv


@pytest.fixture()
def invitee(db):
    from allauth.account.models import EmailAddress

    from apps.accounts.models import User

    user = baker.make(
        User,
        email="jim.halpert@dundermifflin.com",
        first_name="Jim",
        last_name="Halpert",
    )
    user.set_password("dundermifflin")
    user.save()
    EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)
    return user


class TestInviteFlow:
    def test_invite_page_shows_org_and_sender(self, page: Page, live_server, invite):
        page.goto(f"{live_server.url}/organizations/invite/{invite.key}/accept/")

        expect(page.get_by_text("You're invited!")).to_be_visible()
        expect(page.get_by_text("Dunder Mifflin")).to_be_visible()
        # Anonymous visitor sees the create-account / sign-in CTAs
        expect(page.get_by_role("button", name="Create an account to join")).to_be_visible()
        expect(page.get_by_role("button", name="I already have an account")).to_be_visible()

    def test_invalid_key_shows_unavailable(self, page: Page, live_server, db):
        page.goto(f"{live_server.url}/organizations/invite/abc123notarealkey/accept/")

        expect(page.get_by_text("Invitation unavailable")).to_be_visible()

    def test_expired_invite_shown_as_expired(self, page: Page, live_server, expired_invite):
        page.goto(f"{live_server.url}/organizations/invite/{expired_invite.key}/accept/")

        expect(page.get_by_text("Invitation expired")).to_be_visible()

    def test_existing_user_can_accept(self, page: Page, live_server, invite, invitee):
        # Sign in as the invitee, then visit the accept link.
        page.goto(f"{live_server.url}/accounts/login/")
        page.get_by_placeholder("Email").fill("jim.halpert@dundermifflin.com")
        page.get_by_placeholder("Password").fill("dundermifflin")
        page.get_by_role("button", name="Sign In", exact=True).click()
        page.wait_for_url(f"{live_server.url}/", timeout=10000)

        page.goto(f"{live_server.url}/organizations/invite/{invite.key}/accept/")
        expect(page.get_by_text("You're invited!")).to_be_visible()

        page.get_by_role("button", name="Accept invitation").click()

        expect(page.get_by_text(re.compile(r"You've joined Dunder Mifflin"))).to_be_visible(timeout=10000)

        # The invite is consumed and the user is now a member.
        from apps.organizations.models import OrganizationInvite, OrganizationMember

        assert not OrganizationInvite.objects.filter(pk=invite.pk).exists()
        assert OrganizationMember.objects.filter(
            organization=invite.organization, user=invitee
        ).exists()

    def test_decline_consumes_invite(self, page: Page, live_server, invite):
        page.goto(f"{live_server.url}/organizations/invite/{invite.key}/accept/")
        # Sign in first so the Decline button is visible (auth gate).
        # The decline endpoint itself doesn't require auth; for this test we
        # exercise the unauthenticated path: hit the API directly.
        resp = page.request.post(f"{live_server.url}/api/invite-by-key/{invite.key}/decline/")
        assert resp.status == 200

        from apps.organizations.models import OrganizationInvite

        assert not OrganizationInvite.objects.filter(pk=invite.pk).exists()

    def test_unauthenticated_accept_redirects_to_login(self, page: Page, live_server, invite):
        page.goto(f"{live_server.url}/accounts/login/")
        # Confirm baseline: the login page rendered.
        expect(page.get_by_placeholder("Email")).to_be_visible()

        # Visit the invite page as an anonymous visitor and click the
        # "I already have an account" path; we expect to land on login with
        # the invite URL preserved as ?next=.
        page.goto(f"{live_server.url}/organizations/invite/{invite.key}/accept/")
        page.get_by_role("button", name="I already have an account").click()

        expect(page).to_have_url(
            re.compile(rf"/accounts/login/.*next=.*{re.escape(invite.key)}")
        )
