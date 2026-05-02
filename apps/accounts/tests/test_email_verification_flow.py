"""
Exercise the headless email-verify endpoint.

Covers the key that comes out of the verification email and confirms the
signed key survives the full login → email → verify round trip.
"""

import json
import re
from urllib.parse import unquote

import pytest
from allauth.account.models import EmailAddress, EmailConfirmationHMAC

from apps.accounts.models import User


@pytest.fixture()
def unverified_user(db):
    user = User.objects.create(
        email="test-verify@example.com",
        username="test-verify@example.com",
    )
    user.set_password("testpw123!")
    user.save()
    EmailAddress.objects.create(user=user, email=user.email, verified=False, primary=True)
    return user


def _extract_key_from_email(body: str) -> str:
    match = re.search(r"http\S*/accounts/confirm-email/(\S+)", body)
    assert match, f"verification link not found in email body:\n{body}"
    return match.group(1).rstrip("/").rstrip(">").rstrip(".")


@pytest.mark.django_db
def test_login_triggers_verification_email_with_usable_key(mailoutbox, client, unverified_user, settings):
    settings.AUTHENTICATION_BACKENDS = ["allauth.account.auth_backends.AuthenticationBackend"]
    settings.ACCOUNT_EMAIL_VERIFICATION = "mandatory"

    login_response = client.post(
        "/_allauth/browser/v1/auth/login",
        data={"email": unverified_user.email, "password": "testpw123!"},
        content_type="application/json",
    )
    assert login_response.status_code == 401
    assert len(mailoutbox) == 1

    encoded_key = _extract_key_from_email(mailoutbox[0].body)

    # Regression: allauth renders the key through urllib.parse.quote() before
    # embedding it in the email URL, so the raw segment after the last `/` is
    # percent-encoded. allauth.from_key() only accepts the decoded form.
    assert EmailConfirmationHMAC.from_key(encoded_key) is None
    decoded_key = unquote(encoded_key)
    assert EmailConfirmationHMAC.from_key(decoded_key) is not None


@pytest.mark.django_db
def test_verify_endpoint_accepts_decoded_key(mailoutbox, client, unverified_user, settings):
    """
    Mirror what EmailConfirmView.vue does.

    decodeURIComponent the route param before POSTing to
    /_allauth/browser/v1/auth/email/verify.
    """
    settings.AUTHENTICATION_BACKENDS = ["allauth.account.auth_backends.AuthenticationBackend"]
    settings.ACCOUNT_EMAIL_VERIFICATION = "mandatory"

    client.post(
        "/_allauth/browser/v1/auth/login",
        data={"email": unverified_user.email, "password": "testpw123!"},
        content_type="application/json",
    )
    decoded_key = unquote(_extract_key_from_email(mailoutbox[0].body))

    verify_response = client.post(
        "/_allauth/browser/v1/auth/email/verify",
        data={"key": decoded_key},
        content_type="application/json",
    )
    assert verify_response.status_code in (200, 401), (
        f"expected 200/401 (verified, pending login), got {verify_response.status_code}: {verify_response.content!r}"
    )
    assert EmailAddress.objects.get(user=unverified_user).verified is True


@pytest.mark.django_db
def test_set_primary_email_uses_patch(client):
    """
    Mark-as-primary uses PATCH so allauth's headless API doesn't resend a verification email.

    AccountEmailView.vue calls setPrimaryEmail() to swap which verified email
    is primary. allauth's headless ManageEmailView maps PATCH → mark-as-primary
    and PUT → resend-verification, so the SPA must use PATCH or the click
    silently re-sends a verification email instead of changing the primary.
    """
    user = User.objects.create(email="primary@example.com", username="primary@example.com")
    user.set_password("testpw123!")
    user.save()
    EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)
    secondary = EmailAddress.objects.create(
        user=user,
        email="secondary@example.com",
        verified=True,
        primary=False,
    )

    client.force_login(user)
    response = client.patch(
        "/_allauth/browser/v1/account/email",
        data=json.dumps({"email": secondary.email, "primary": True}),
        content_type="application/json",
    )

    assert response.status_code == 200, response.content
    secondary.refresh_from_db()
    assert secondary.primary is True
    assert EmailAddress.objects.get(email="primary@example.com").primary is False
