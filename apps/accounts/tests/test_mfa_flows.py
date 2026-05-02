"""Happy-path coverage for the allauth headless MFA endpoints (TOTP + recovery codes)."""

import pyotp
import pytest
from allauth.account.models import EmailAddress
from allauth.mfa.models import Authenticator
from allauth.mfa.recovery_codes.internal.auth import RecoveryCodes
from allauth.mfa.totp.internal.auth import TOTP, generate_totp_secret

from apps.accounts.models import User


@pytest.fixture()
def verified_user(db):
    user = User.objects.create(email="mfa@example.com", username="mfa@example.com")
    user.set_password("testpw123!")
    user.save()
    EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)
    return user


@pytest.fixture(autouse=True)
def _use_allauth_backend(settings):
    settings.AUTHENTICATION_BACKENDS = ["allauth.account.auth_backends.AuthenticationBackend"]


def _login(client, user):
    resp = client.post(
        "/_allauth/browser/v1/auth/login",
        data={"email": user.email, "password": "testpw123!"},
        content_type="application/json",
    )
    assert resp.status_code == 200, resp.content


@pytest.mark.django_db
def test_totp_setup_returns_secret_and_url(client, verified_user):
    _login(client, verified_user)
    resp = client.get("/_allauth/browser/v1/account/authenticators/totp")
    assert resp.status_code == 404, resp.content
    body = resp.json()
    assert "secret" in body["meta"]
    assert body["meta"]["totp_url"].startswith("otpauth://")


@pytest.mark.django_db
def test_totp_activate_then_login_requires_code(client, verified_user, mailoutbox):
    _login(client, verified_user)

    setup = client.get("/_allauth/browser/v1/account/authenticators/totp").json()
    secret = setup["meta"]["secret"]
    code = pyotp.TOTP(secret).now()

    activate = client.post(
        "/_allauth/browser/v1/account/authenticators/totp",
        data={"code": code},
        content_type="application/json",
    )
    assert activate.status_code == 200, activate.content
    assert Authenticator.objects.filter(user=verified_user, type=Authenticator.Type.TOTP).exists()

    # Activation should also create recovery codes
    assert Authenticator.objects.filter(
        user=verified_user,
        type=Authenticator.Type.RECOVERY_CODES,
    ).exists()

    # Subsequent login returns 401 with a pending mfa_authenticate flow
    client.post("/_allauth/browser/v1/auth/session", content_type="application/json")  # logout
    client.cookies.clear()
    resp = client.post(
        "/_allauth/browser/v1/auth/login",
        data={"email": verified_user.email, "password": "testpw123!"},
        content_type="application/json",
    )
    assert resp.status_code == 401, resp.content
    flows = resp.json().get("data", {}).get("flows", [])
    assert any(f["id"] == "mfa_authenticate" for f in flows)

    # Submitting the TOTP code completes the login
    code = pyotp.TOTP(secret).now()
    finish = client.post(
        "/_allauth/browser/v1/auth/2fa/authenticate",
        data={"code": code},
        content_type="application/json",
    )
    assert finish.status_code == 200, finish.content
    assert client.session.get("_auth_user_id") == str(verified_user.pk)


@pytest.mark.django_db
def test_recovery_code_consumes_one(client, verified_user):
    # Pre-seed TOTP + recovery codes so we don't need the activation flow
    TOTP.activate(verified_user, generate_totp_secret())
    RecoveryCodes.activate(verified_user)
    rc_authenticator = Authenticator.objects.get(
        user=verified_user,
        type=Authenticator.Type.RECOVERY_CODES,
    )
    unused_before = rc_authenticator.wrap().get_unused_codes()
    assert len(unused_before) > 0

    resp = client.post(
        "/_allauth/browser/v1/auth/login",
        data={"email": verified_user.email, "password": "testpw123!"},
        content_type="application/json",
    )
    assert resp.status_code == 401, resp.content

    used = unused_before[0]
    finish = client.post(
        "/_allauth/browser/v1/auth/2fa/authenticate",
        data={"code": used},
        content_type="application/json",
    )
    assert finish.status_code == 200, finish.content

    rc_authenticator.refresh_from_db()
    unused_after = rc_authenticator.wrap().get_unused_codes()
    assert len(unused_after) == len(unused_before) - 1
    assert used not in unused_after


@pytest.mark.django_db
def test_authenticators_list(client, verified_user):
    secret = generate_totp_secret()
    TOTP.activate(verified_user, secret)
    RecoveryCodes.activate(verified_user)

    client.post(
        "/_allauth/browser/v1/auth/login",
        data={"email": verified_user.email, "password": "testpw123!"},
        content_type="application/json",
    )
    client.post(
        "/_allauth/browser/v1/auth/2fa/authenticate",
        data={"code": pyotp.TOTP(secret).now()},
        content_type="application/json",
    )

    resp = client.get("/_allauth/browser/v1/account/authenticators")
    assert resp.status_code == 200, resp.content
    types = {a["type"] for a in resp.json()["data"]}
    assert "totp" in types
    assert "recovery_codes" in types


@pytest.mark.django_db
def test_passkey_login_endpoint_advertised_in_config(client):
    resp = client.get("/_allauth/browser/v1/config")
    assert resp.status_code == 200, resp.content
    mfa = resp.json().get("data", {}).get("mfa", {})
    assert mfa.get("passkey_login_enabled") is True
    assert "webauthn" in mfa.get("supported_types", [])
