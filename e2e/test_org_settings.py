"""
End-to-end tests for the organization settings pages (/organizations/<slug>/settings/...).

Every tab's API is owner-only. The Members and Teams tabs load lists that the API
paginates (`DEFAULT_PAGE_SIZE` rows per page), so they must follow every page.
"""

import re
from datetime import timedelta

import pytest
from model_bakery import baker
from playwright.sync_api import Page, expect


def _sign_in(page: Page, live_server, email: str, next_path: str):
    page.goto(f"{live_server.url}/accounts/login/?next={next_path}")
    page.get_by_placeholder("Email").fill(email)
    page.get_by_placeholder("Password").fill("dundermifflin")
    page.get_by_role("button", name="Sign In", exact=True).click()
    page.wait_for_url(re.compile(r"^(?!.*/accounts/login/)"), timeout=10000)


@pytest.fixture()
def org(db, user):
    from apps.organizations.models import Organization, OrganizationMember

    org = Organization.objects.create(name="Dunder Mifflin", slug="dunder-mifflin")
    OrganizationMember.objects.create(organization=org, user=user, is_owner=True, is_primary=True)
    return org


@pytest.fixture()
def more_than_a_page():
    from django.conf import settings

    return settings.DEFAULT_PAGE_SIZE + 5


@pytest.fixture()
def employees(org, more_than_a_page):
    from apps.accounts.models import User
    from apps.organizations.models import OrganizationMember

    users = User.objects.bulk_create(
        User(username=f"employee{i:03d}", email=f"employee{i:03d}@dundermifflin.com", first_name="Employee")
        for i in range(more_than_a_page)
    )
    OrganizationMember.objects.bulk_create(OrganizationMember(organization=org, user=u) for u in users)
    return users


class TestMembersTab:
    MEMBERS_PATH = "/organizations/dunder-mifflin/settings/members/"

    def test_lists_members_past_the_first_page(self, page: Page, live_server, employees, more_than_a_page):
        _sign_in(page, live_server, "michael.scott@dundermifflin.com", self.MEMBERS_PATH)

        expect(page.get_by_text(re.compile(r"^employee\d+@dundermifflin\.com$"))).to_have_count(more_than_a_page)

    def test_lists_invites_past_the_first_page(self, page: Page, live_server, org, user, more_than_a_page):
        from apps.organizations.models import OrganizationInvite

        OrganizationInvite.objects.bulk_create(
            OrganizationInvite(
                organization=org, sender=user, invitee_email=f"guest{i:03d}@dundermifflin.com", key=f"{i:032d}"
            )
            for i in range(more_than_a_page)
        )

        _sign_in(page, live_server, "michael.scott@dundermifflin.com", self.MEMBERS_PATH)

        expect(page.get_by_text(re.compile(r"^guest\d+@dundermifflin\.com$"))).to_have_count(more_than_a_page)

    def test_badges_expired_invites(self, page: Page, live_server, org, user):
        from django.utils import timezone

        from apps.organizations.models import OrganizationInvite

        OrganizationInvite.objects.create(organization=org, sender=user, invitee_email="jim.halpert@dundermifflin.com")
        expired = OrganizationInvite.objects.create(
            organization=org, sender=user, invitee_email="pam.beesly@dundermifflin.com"
        )
        OrganizationInvite.objects.filter(pk=expired.pk).update(
            created=timezone.now() - timedelta(days=OrganizationInvite.expired_in_days + 1)
        )

        _sign_in(page, live_server, "michael.scott@dundermifflin.com", self.MEMBERS_PATH)

        pending_row = page.get_by_role("row").filter(has_text="jim.halpert@dundermifflin.com")
        expired_row = page.get_by_role("row").filter(has_text="pam.beesly@dundermifflin.com")
        expect(pending_row.get_by_text("Pending", exact=True)).to_be_visible()
        expect(expired_row.get_by_text("Expired", exact=True)).to_be_visible()
        expect(expired_row.get_by_text("Pending", exact=True)).to_have_count(0)


class TestTeamsTab:
    def test_lists_teams_past_the_first_page(self, page: Page, live_server, org, more_than_a_page):
        from apps.teams.models import Team

        Team.objects.bulk_create(Team(organization=org, name=f"Team {i:03d}") for i in range(more_than_a_page))

        _sign_in(page, live_server, "michael.scott@dundermifflin.com", "/organizations/dunder-mifflin/settings/teams/")

        expect(page.get_by_text(re.compile(r"^Team \d{3}$"))).to_have_count(more_than_a_page)


class TestNonOwner:
    @pytest.fixture()
    def member(self, org):
        from allauth.account.models import EmailAddress

        from apps.accounts.models import User
        from apps.organizations.models import OrganizationMember

        member = baker.make(User, email="dwight.schrute@dundermifflin.com", first_name="Dwight", last_name="Schrute")
        member.set_password("dundermifflin")
        member.save()
        EmailAddress.objects.create(user=member, email=member.email, verified=True, primary=True)
        OrganizationMember.objects.create(organization=org, user=member, is_primary=True)
        return member

    @pytest.mark.parametrize("tab", ["general", "members", "teams"])
    def test_settings_redirect_home(self, page: Page, live_server, member, tab):
        # The settings APIs are owner-only; a member who types the URL used to get "No members." and an invite form.
        _sign_in(page, live_server, member.email, f"/organizations/dunder-mifflin/settings/{tab}/")

        expect(page).to_have_url(f"{live_server.url}/")
        expect(page.get_by_text("Invite a Member")).to_have_count(0)
