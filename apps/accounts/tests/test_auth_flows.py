"""
Happy-path coverage for the allauth headless auth endpoints.

Mirrors the style in test_email_verification_flow.py.
"""

from django.core import mail
from django.test import override_settings

import pytest

from apps.accounts.models import User
from apps.accounts.recipes import make_user
from apps.base.tests import BaseTest
from apps.base.tests.mail import record_queued_emails, use_failing_mail_server
from apps.base.tests.sign_in import api_sign_in

SIGNUP_URL = "/_allauth/browser/v1/auth/signup"
RESET_REQUEST_URL = "/_allauth/browser/v1/auth/password/request"


# ACCOUNT_SIGNUP_OPEN reads from env and defaults False in CI, which makes the signup endpoint 403.
@override_settings(ACCOUNT_SIGNUP_OPEN=True)
class TestAuthFlows(BaseTest):
    @classmethod
    def setUpTestData(cls):
        cls.user = make_user("ready@example.com")

    def test_signup(self):
        resp = self.client.post(
            SIGNUP_URL,
            data={"email": "newbie@example.com", "password": "testpw123!"},
            content_type="application/json",
        )
        # Signup immediately gates behind email verification — 401 signals "pending verify"
        assert resp.status_code in (200, 401), resp.content
        assert User.objects.filter(email="newbie@example.com").exists()
        assert len(mail.outbox) == 1
        assert "newbie@example.com" in mail.outbox[0].to

    def test_login(self):
        resp = api_sign_in(self.client, self.user.email)
        assert resp.status_code == 200, resp.content
        assert self.client.session.get("_auth_user_id") == str(self.user.pk)

    def test_login_with_a_wrong_password_is_refused(self):
        resp = api_sign_in(self.client, self.user.email, "not-the-password")

        assert resp.status_code == 400, resp.content
        [error] = resp.json()["errors"]
        assert error["message"] == "The email address and/or password you specified are not correct."
        assert error["param"] == "password"
        assert "_auth_user_id" not in self.client.session
        assert self.client.get("/api/app-context/").json()["user"] is None

    def test_password_reset_request(self):
        resp = self.client.post(RESET_REQUEST_URL, data={"email": self.user.email}, content_type="application/json")
        assert resp.status_code in (200, 401), resp.content
        assert len(mail.outbox) == 1
        assert self.user.email in mail.outbox[0].to


@override_settings(ACCOUNT_SIGNUP_OPEN=True)
class TestMailOutage(BaseTest):
    """allauth's emails are queued (`AccountAdapter.send_mail`), so a mail server that's down can't fail the request."""

    @classmethod
    def setUpTestData(cls):
        cls.user = make_user("ready@example.com")

    @pytest.fixture(autouse=True)
    def _pytest_fixtures(self, settings, monkeypatch):
        use_failing_mail_server(settings)
        self.queued = record_queued_emails(monkeypatch)

    def test_password_reset_request(self):
        resp = self.client.post(RESET_REQUEST_URL, data={"email": self.user.email}, content_type="application/json")

        assert resp.status_code == 200, resp.content
        [message] = self.queued
        assert message["to"] == [self.user.email]
        assert "/accounts/password/reset/key/" in message["body"]

    def test_signup(self):
        resp = self.client.post(
            SIGNUP_URL,
            data={"email": "newbie@example.com", "password": "testpw123!"},
            content_type="application/json",
        )

        # Email verification is optional, so the new user is signed in at once.
        assert resp.status_code == 200, resp.content
        [message] = self.queued
        assert message["to"] == ["newbie@example.com"]
        assert "/accounts/confirm-email/" in message["body"]
