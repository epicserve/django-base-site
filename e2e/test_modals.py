"""End-to-end tests for AppModal, the dialog every modal in the SPA is built on."""

import re

import pytest
from playwright.sync_api import Page, expect


class TestAppModal:
    @pytest.fixture()
    def org(self, user):
        from apps.organizations.models import Organization, OrganizationMember
        from apps.organizations.roles import OrgRole

        org = Organization.objects.create(name="Dunder Mifflin", slug="dunder-mifflin")
        OrganizationMember.objects.create(organization=org, user=user, role=OrgRole.OWNER, is_primary=True)
        return org

    def test_the_close_button_has_a_name(self, page: Page, live_server, org):
        # It held only an icon, so a screen reader announced an unnamed button.
        page.goto(f"{live_server.url}/accounts/login/")
        page.get_by_placeholder("Email").fill("michael.scott@dundermifflin.com")
        page.get_by_placeholder("Password").fill("dundermifflin")
        page.get_by_role("button", name="Sign In", exact=True).click()
        page.wait_for_url(re.compile(r"^(?!.*/accounts/login/)"), timeout=10000)
        page.goto(f"{live_server.url}/organizations/dunder-mifflin/settings/members/")
        page.get_by_role("button", name="Invite by Email").click()
        dialog = page.get_by_role("dialog", name="Invite by Email")
        expect(dialog).to_be_visible()

        dialog.get_by_role("button", name="Close", exact=True).click()

        expect(dialog).not_to_be_visible()
