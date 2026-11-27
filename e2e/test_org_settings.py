"""
End-to-end tests for the organization settings pages (/organizations/<slug>/settings/...).

Each tab's API needs a permission that only the owner role grants (apps/organizations/roles.py). The Members and
Teams tabs load lists that the API paginates (`DEFAULT_PAGE_SIZE` rows per page), so they must follow every page;
`getAllResults()` itself is covered in frontend/js/utils/api.test.ts.
"""

import re

import pytest
from playwright.sync_api import Page, expect

MEMBERS_PATH = "/organizations/dunder-mifflin/settings/members/"
TEAMS_PATH = "/organizations/dunder-mifflin/settings/teams/"


@pytest.fixture()
def more_than_a_page():
    from django.conf import settings

    return settings.DEFAULT_PAGE_SIZE + 5


@pytest.fixture()
def dwight(org):
    from apps.accounts.recipes import make_user
    from apps.organizations.recipes import make_member

    return make_member(org, make_user("dwight.schrute@dundermifflin.com", first_name="Dwight", last_name="Schrute"))


class TestMembersTab:
    def test_lists_every_page(self, page: Page, live_server, sign_in, org, user, more_than_a_page, subtests):
        from apps.accounts.models import User
        from apps.organizations.models import OrganizationInvite, OrganizationMember
        from apps.teams.models import Team

        employees = User.objects.bulk_create(
            User(username=f"employee{i:03d}", email=f"employee{i:03d}@dundermifflin.com", first_name="Employee")
            for i in range(more_than_a_page)
        )
        OrganizationMember.objects.bulk_create(OrganizationMember(organization=org, user=u) for u in employees)
        OrganizationInvite.objects.bulk_create(
            OrganizationInvite(
                organization=org, sender=user, invitee_email=f"guest{i:03d}@dundermifflin.com", key=f"{i:032d}"
            )
            for i in range(more_than_a_page)
        )
        Team.objects.bulk_create(Team(organization=org, name=f"Team {i:03d}") for i in range(more_than_a_page))
        sign_in(user, MEMBERS_PATH)

        with subtests.test("members"):
            expect(page.get_by_text(re.compile(r"^employee\d+@dundermifflin\.com$"))).to_have_count(more_than_a_page)

        with subtests.test("invites"):
            expect(page.get_by_text(re.compile(r"^guest\d+@dundermifflin\.com$"))).to_have_count(more_than_a_page)

        with subtests.test("teams"):
            page.goto(f"{live_server.url}{TEAMS_PATH}")
            expect(page.get_by_text(re.compile(r"^Team \d{3}$"))).to_have_count(more_than_a_page)

    def test_invites(self, page: Page, sign_in, org, user, subtests):
        from apps.accounts.recipes import make_user
        from apps.organizations.recipes import make_invite

        make_invite(org, user, email="jim.halpert@dundermifflin.com")
        make_invite(org, user, email="pam.beesly@dundermifflin.com", expired=True)
        dwight = make_user("dwight.schrute@dundermifflin.com", first_name="Dwight", last_name="Schrute")
        make_invite(org, user, invitee=dwight)
        sign_in(user, MEMBERS_PATH)

        with subtests.test("badges pending and expired invites"):
            pending_row = page.get_by_role("row").filter(has_text="jim.halpert@dundermifflin.com")
            expired_row = page.get_by_role("row").filter(has_text="pam.beesly@dundermifflin.com")
            expect(pending_row.get_by_text("Pending", exact=True)).to_be_visible()
            expect(expired_row.get_by_text("Expired", exact=True)).to_be_visible()
            expect(expired_row.get_by_text("Pending", exact=True)).to_have_count(0)

        with subtests.test("names an invitee who has an account"):
            invite_row = page.get_by_role("row").filter(has_text="dwight.schrute@dundermifflin.com")
            expect(invite_row.get_by_text("Dwight Schrute", exact=True)).to_be_visible()


class TestChangeRole:
    def test_an_owner_makes_a_member_an_owner(self, page: Page, sign_in, org, user, dwight):
        from apps.organizations.models import OrganizationMember
        from apps.organizations.roles import OrgRole

        sign_in(user, MEMBERS_PATH)
        row = page.get_by_role("row", name=re.compile("dwight.schrute@dundermifflin.com"))
        expect(row.get_by_text("Member", exact=True)).to_be_visible()

        row.get_by_role("button", name="Change Role").click()
        dialog = page.get_by_role("dialog")
        expect(dialog).to_contain_text("Change Dwight Schrute's role from member to owner?")
        dialog.get_by_role("button", name="OK").click()

        expect(row.get_by_text("Owner", exact=True)).to_be_visible()
        assert OrganizationMember.objects.get(organization=org, user=dwight).role == OrgRole.OWNER


class TestNonOwner:
    def test_org_menu_hides_settings_link(self, page: Page, sign_in, dwight):
        sign_in(dwight, "/")

        page.get_by_role("button", name="Dunder Mifflin").click()

        expect(page.get_by_role("link", name="Settings", exact=True)).to_have_count(0)
        # The UI calls it an organization everywhere, as in "Create Organization".
        page.get_by_role("link", name="Switch Organization", exact=True).click()
        expect(page.get_by_role("heading", name="Switch Organization", exact=True)).to_be_visible()

    def test_settings_redirect_home(self, page: Page, live_server, sign_in, dwight):
        # The settings APIs are owner-only; a member who types the URL used to get "No members." and an invite form.
        # frontend/js/utils/routeGuard.test.ts covers every tab; this checks the router uses it.
        sign_in(dwight, MEMBERS_PATH)

        expect(page).to_have_url(f"{live_server.url}/")
        expect(page.get_by_text("Invite a Member")).to_have_count(0)
