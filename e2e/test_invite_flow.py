"""
End-to-end tests for the organization invitation flow.

Covers the SPA-driven accept-invite page that the invitation email links to:

  /organizations/invite/<key>/accept/

The page is a Vue route served via SPAView; invite metadata loads from
/api/invite-by-key/<key>/, and accept/decline POST to the same prefix.
"""

import re

import pytest
from playwright.sync_api import Page, expect


@pytest.fixture()
def invite(org, user):
    from apps.organizations.tests.recipes import make_invite

    return make_invite(org, user, email="jim.halpert@dundermifflin.com")


@pytest.fixture()
def invitee(db):
    from apps.accounts.tests.recipes import make_user

    return make_user("jim.halpert@dundermifflin.com", first_name="Jim", last_name="Halpert")


class TestInviteFlow:
    def test_the_invite_page(self, page: Page, live_server, org, user, invite, subtests):
        # Each case only reads, so they share one browser and database.
        from apps.organizations.tests.recipes import make_invite

        with subtests.test("an anonymous visitor sees the organization and sender"):
            page.goto(f"{live_server.url}/organizations/invite/{invite.key}/accept/")

            expect(page.get_by_text("You're Invited!")).to_be_visible()
            # The period comes from sentencePeriod(), which frontend/js/utils/format.test.ts covers for a name that
            # already ends in one.
            sentence = page.get_by_text("invited you to join")
            expect(sentence).to_have_text("Michael Scott invited you to join Dunder Mifflin.")
            expect(page.get_by_role("button", name="Create an Account to Join")).to_be_visible()
            expect(page.get_by_role("button", name="I Already Have an Account")).to_be_visible()

        with subtests.test("an unknown key"):
            page.goto(f"{live_server.url}/organizations/invite/abc123notarealkey/accept/")

            expect(page.get_by_text("Invitation Unavailable")).to_be_visible()

        with subtests.test("an expired invite"):
            expired = make_invite(org, user, email="pam.beesly@dundermifflin.com", expired=True)
            page.goto(f"{live_server.url}/organizations/invite/{expired.key}/accept/")

            expect(page.get_by_text("Invitation Expired")).to_be_visible()

    def test_existing_user_can_accept(self, page: Page, sign_in, invite, invitee):
        sign_in(invitee, f"/organizations/invite/{invite.key}/accept/")
        expect(page.get_by_text("You're Invited!")).to_be_visible()

        page.get_by_role("button", name="Accept Invitation").click()

        expect(page.get_by_text(re.compile(r"You've Joined Dunder Mifflin"))).to_be_visible(timeout=10000)

        # The invite is consumed and the user is now a member.
        from apps.organizations.models import OrganizationInvite, OrganizationMember

        assert not OrganizationInvite.objects.filter(pk=invite.pk).exists()
        assert OrganizationMember.objects.filter(organization=invite.organization, user=invitee).exists()

    def test_decline_consumes_invite(self, page: Page, sign_in, invite, invitee):
        # Signed in as the invitee, so the Decline button shows.
        sign_in(invitee, f"/organizations/invite/{invite.key}/accept/")
        expect(page.get_by_text("You're Invited!")).to_be_visible()

        page.get_by_role("button", name="Decline").click()

        expect(page.get_by_text("Invitation Declined")).to_be_visible(timeout=10000)

        from apps.organizations.models import OrganizationInvite

        assert not OrganizationInvite.objects.filter(pk=invite.pk).exists()

    def test_unauthenticated_accept_redirects_to_login(self, page: Page, live_server, invite):
        # Visit the invite page as an anonymous visitor and click the
        # "I Already Have an Account" path; we expect to land on login with
        # the invite URL preserved as ?next=.
        page.goto(f"{live_server.url}/organizations/invite/{invite.key}/accept/")
        page.get_by_role("button", name="I Already Have an Account").click()

        expect(page).to_have_url(re.compile(rf"/accounts/login/.*next=.*{re.escape(invite.key)}"))
