"""
Happy-path coverage for the allauth headless auth endpoints.

Mirrors the style in test_email_verification_flow.py.
"""

import pytest
from allauth.account.models import EmailAddress

from apps.accounts.models import User


@pytest.fixture()
def verified_user(db):
    user = User.objects.create(email="ready@example.com", username="ready@example.com")
    user.set_password("testpw123!")
    user.save()
    EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)
    return user


@pytest.fixture(autouse=True)
def _use_allauth_backend(settings):
    # Test runner defaults to ModelBackend (username-based). Switch to allauth's
    # backend so email-based login/signup endpoints work end-to-end.
    settings.AUTHENTICATION_BACKENDS = ["allauth.account.auth_backends.AuthenticationBackend"]
    # ACCOUNT_SIGNUP_OPEN reads from env and defaults False in CI, which makes
    # the signup endpoint 403. Force it on for this test module.
    settings.ACCOUNT_SIGNUP_OPEN = True


@pytest.mark.django_db
def test_signup(mailoutbox, client):
    resp = client.post(
        "/_allauth/browser/v1/auth/signup",
        data={"email": "newbie@example.com", "password": "testpw123!"},
        content_type="application/json",
    )
    # Signup immediately gates behind email verification — 401 signals "pending verify"
    assert resp.status_code in (200, 401), resp.content
    assert User.objects.filter(email="newbie@example.com").exists()
    assert len(mailoutbox) == 1
    assert "newbie@example.com" in mailoutbox[0].to


@pytest.mark.django_db
def test_login(client, verified_user):
    resp = client.post(
        "/_allauth/browser/v1/auth/login",
        data={"email": verified_user.email, "password": "testpw123!"},
        content_type="application/json",
    )
    assert resp.status_code == 200, resp.content
    assert client.session.get("_auth_user_id") == str(verified_user.pk)


@pytest.mark.django_db
def test_password_reset_request(mailoutbox, client, verified_user):
    resp = client.post(
        "/_allauth/browser/v1/auth/password/request",
        data={"email": verified_user.email},
        content_type="application/json",
    )
    assert resp.status_code in (200, 401), resp.content
    assert len(mailoutbox) == 1
    assert verified_user.email in mailoutbox[0].to
