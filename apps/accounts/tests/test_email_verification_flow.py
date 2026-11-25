"""
Exercise the headless email-verify endpoint.

Covers the key that comes out of the verification email and confirms the
signed key survives the full login → email → verify round trip.
"""

import json
import re
from urllib.parse import unquote

from django.core import mail
from django.test import override_settings

from allauth.account.models import EmailAddress, EmailConfirmationHMAC

from apps.accounts.tests.recipes import make_user
from apps.base.tests import BaseTest
from apps.base.tests.sign_in import api_sign_in, sign_in


def _extract_key_from_email(body: str) -> str:
    match = re.search(r"http\S*/accounts/confirm-email/(\S+)", body)
    assert match, f"verification link not found in email body:\n{body}"
    return match.group(1).rstrip("/").rstrip(">").rstrip(".")


@override_settings(ACCOUNT_EMAIL_VERIFICATION="mandatory")
class TestEmailVerification(BaseTest):
    @classmethod
    def setUpTestData(cls):
        cls.unverified_user = make_user("test-verify@example.com", verified=False)

    def test_login_triggers_verification_email_with_usable_key(self):
        login_response = api_sign_in(self.client, self.unverified_user.email)
        assert login_response.status_code == 401
        assert len(mail.outbox) == 1

        encoded_key = _extract_key_from_email(mail.outbox[0].body)

        # Regression: allauth renders the key through urllib.parse.quote() before
        # embedding it in the email URL, so the raw segment after the last `/` is
        # percent-encoded. allauth.from_key() only accepts the decoded form.
        assert EmailConfirmationHMAC.from_key(encoded_key) is None
        decoded_key = unquote(encoded_key)
        assert EmailConfirmationHMAC.from_key(decoded_key) is not None

    def test_verify_endpoint_accepts_decoded_key(self):
        """
        Mirror what EmailConfirmView.vue does.

        decodeURIComponent the route param before POSTing to
        /_allauth/browser/v1/auth/email/verify.
        """
        api_sign_in(self.client, self.unverified_user.email)
        decoded_key = unquote(_extract_key_from_email(mail.outbox[0].body))

        verify_response = self.client.post(
            "/_allauth/browser/v1/auth/email/verify",
            data={"key": decoded_key},
            content_type="application/json",
        )
        assert verify_response.status_code in (200, 401), (
            "expected 200/401 (verified, pending login), "
            f"got {verify_response.status_code}: {verify_response.content!r}"
        )
        assert EmailAddress.objects.get(user=self.unverified_user).verified is True


class TestSetPrimaryEmail(BaseTest):
    @classmethod
    def setUpTestData(cls):
        cls.user = make_user("primary@example.com")
        cls.secondary = EmailAddress.objects.create(
            user=cls.user,
            email="secondary@example.com",
            verified=True,
            primary=False,
        )

    def test_set_primary_email_uses_patch(self):
        """
        Mark-as-primary uses PATCH so allauth's headless API doesn't resend a verification email.

        AccountEmailView.vue calls setPrimaryEmail() to swap which verified email
        is primary. allauth's headless ManageEmailView maps PATCH → mark-as-primary
        and PUT → resend-verification, so the SPA must use PATCH or the click
        silently re-sends a verification email instead of changing the primary.
        """
        sign_in(self.client, self.user)
        response = self.client.patch(
            "/_allauth/browser/v1/account/email",
            data=json.dumps({"email": self.secondary.email, "primary": True}),
            content_type="application/json",
        )

        assert response.status_code == 200, response.content
        self.secondary.refresh_from_db()
        assert self.secondary.primary is True
        assert EmailAddress.objects.get(email="primary@example.com").primary is False
