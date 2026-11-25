"""
The pages break no part of the Content-Security-Policy, so it can be enforced.

The policy is report-only: a browser runs whatever it doesn't allow, and fires a `securitypolicyviolation` event. These
tests fail on any such event, so a change that needs a new source has to add it to `content_security_policy()` in
config/settings/_base.py. They load the built assets; the Vite dev server's allowances are checked by hand.
"""

import base64
import re

import pytest
from playwright.sync_api import Page, expect

RECORD_VIOLATIONS = """
document.addEventListener('securitypolicyviolation', (event) =>
  window.recordViolation(
    `${location.pathname}: ${event.violatedDirective} blocked ${event.blockedURI || 'inline'} ${event.sample}`.trim(),
  ),
);
"""

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


@pytest.fixture()
def violations(page: Page) -> list[str]:
    found: list[str] = []
    page.expose_function("recordViolation", lambda violation: found.append(violation))
    page.add_init_script(RECORD_VIOLATIONS)
    return found


def _visit(page: Page, url: str):
    page.goto(url)
    page.wait_for_load_state("networkidle")


class TestNoPageBreaksThePolicy:
    def test_signed_out_pages(self, page: Page, live_server, violations):
        for path in ["/accounts/login/", "/accounts/signup/", "/accounts/password/reset/"]:
            _visit(page, f"{live_server.url}{path}")

        assert violations == []

    def test_signed_in_pages(self, page: Page, live_server, user, violations):
        from apps.organizations.models import Organization, OrganizationMember
        from apps.organizations.roles import OrgRole

        org = Organization.objects.create(name="Dunder Mifflin", slug="dunder-mifflin")
        OrganizationMember.objects.create(organization=org, user=user, role=OrgRole.OWNER, is_primary=True)
        page.goto(f"{live_server.url}/accounts/login/")
        page.get_by_placeholder("Email").fill("michael.scott@dundermifflin.com")
        page.get_by_placeholder("Password").fill("dundermifflin")
        page.get_by_role("button", name="Sign In", exact=True).click()
        page.wait_for_url(f"{live_server.url}/", timeout=10000)

        for path in [
            "/",
            "/notifications/",
            "/accounts/general/",
            "/accounts/email/",
            "/accounts/security/",
            # Shows the QR code, an image from /qr/.
            "/accounts/security/totp/",
            "/accounts/security/passkeys/",
            "/accounts/notifications/",
            "/organizations/dunder-mifflin/settings/general/",
            "/organizations/dunder-mifflin/settings/members/",
            "/organizations/dunder-mifflin/settings/teams/",
            "/organizations/create/",
            "/not-a-page/",
        ]:
            _visit(page, f"{live_server.url}{path}")
        # The avatar cropper shows a data: URL copy of the chosen image.
        _visit(page, f"{live_server.url}/accounts/general/")
        page.get_by_role("button", name="Change Photo").click()
        page.locator('input[type="file"]').set_input_files(
            {"name": "michael.png", "mimeType": "image/png", "buffer": PNG}
        )
        expect(page.locator(".vue-advanced-cropper img").first).to_have_attribute(
            "src", re.compile(r"^data:image/png;")
        )

        assert violations == []

    def test_the_admin(self, page: Page, live_server, admin_user, violations):
        _visit(page, f"{live_server.url}/admin/login/")
        # allauth signs people in by email, the admin included.
        page.get_by_label("Username").fill(admin_user.email)
        page.get_by_label("Password").fill("password")
        page.get_by_role("button", name="Log in").click()
        page.wait_for_url(f"{live_server.url}/admin/", timeout=10000)

        for path in ["/admin/", "/admin/accounts/user/", f"/admin/accounts/user/{admin_user.pk}/change/"]:
            _visit(page, f"{live_server.url}{path}")

        assert violations == []
