"""Happy-path coverage for the allauth headless MFA endpoints (TOTP + recovery codes)."""

from allauth.mfa.models import Authenticator

from apps.accounts.recipes import make_totp, make_user
from apps.accounts.tests.totp import current_totp_code
from apps.base.tests import BaseTest
from apps.base.tests.sign_in import api_sign_in

TOTP_URL = "/_allauth/browser/v1/account/authenticators/totp"
TWO_FACTOR_URL = "/_allauth/browser/v1/auth/2fa/authenticate"


class TestTotpSetup(BaseTest):
    @classmethod
    def setUpTestData(cls):
        cls.user = make_user("mfa@example.com")

    def _sign_in_with_password(self):
        resp = api_sign_in(self.client, self.user.email)
        assert resp.status_code == 200, resp.content

    def test_totp_setup_returns_secret_and_url(self):
        self._sign_in_with_password()
        resp = self.client.get(TOTP_URL)
        assert resp.status_code == 404, resp.content
        body = resp.json()
        assert "secret" in body["meta"]
        assert body["meta"]["totp_url"].startswith("otpauth://")

    def test_totp_activate_then_login_requires_code(self):
        self._sign_in_with_password()

        setup = self.client.get(TOTP_URL).json()
        secret = setup["meta"]["secret"]
        code = current_totp_code(secret)

        activate = self.client.post(TOTP_URL, data={"code": code}, content_type="application/json")
        assert activate.status_code == 200, activate.content
        assert Authenticator.objects.filter(user=self.user, type=Authenticator.Type.TOTP).exists()

        # Activation should also create recovery codes
        assert Authenticator.objects.filter(
            user=self.user,
            type=Authenticator.Type.RECOVERY_CODES,
        ).exists()

        # Subsequent login returns 401 with a pending mfa_authenticate flow
        self.client.post("/_allauth/browser/v1/auth/session", content_type="application/json")  # logout
        self.client.cookies.clear()
        resp = api_sign_in(self.client, self.user.email)
        assert resp.status_code == 401, resp.content
        flows = resp.json().get("data", {}).get("flows", [])
        assert any(f["id"] == "mfa_authenticate" for f in flows)

        # Submitting the TOTP code completes the login
        code = current_totp_code(secret)
        finish = self.client.post(TWO_FACTOR_URL, data={"code": code}, content_type="application/json")
        assert finish.status_code == 200, finish.content
        assert self.client.session.get("_auth_user_id") == str(self.user.pk)


class TestWithTotp(BaseTest):
    @classmethod
    def setUpTestData(cls):
        cls.user = make_user("mfa@example.com")
        # TOTP + recovery codes, so the tests don't need the activation flow.
        make_totp(cls.user)
        cls.recovery_codes = Authenticator.objects.get(user=cls.user, type=Authenticator.Type.RECOVERY_CODES)

    def test_recovery_code_consumes_one(self):
        unused_before = self.recovery_codes.wrap().get_unused_codes()
        assert len(unused_before) > 0

        resp = api_sign_in(self.client, self.user.email)
        assert resp.status_code == 401, resp.content

        used = unused_before[0]
        finish = self.client.post(TWO_FACTOR_URL, data={"code": used}, content_type="application/json")
        assert finish.status_code == 200, finish.content

        self.recovery_codes.refresh_from_db()
        unused_after = self.recovery_codes.wrap().get_unused_codes()
        assert len(unused_after) == len(unused_before) - 1
        assert used not in unused_after

    def test_authenticators_list(self):
        self.sign_in(self.user)

        resp = self.client.get("/_allauth/browser/v1/account/authenticators")
        assert resp.status_code == 200, resp.content
        types = {a["type"] for a in resp.json()["data"]}
        assert "totp" in types
        assert "recovery_codes" in types


class TestPasskeyConfig:
    def test_passkey_login_endpoint_advertised_in_config(self, client):
        resp = client.get("/_allauth/browser/v1/config")
        assert resp.status_code == 200, resp.content
        mfa = resp.json().get("data", {}).get("mfa", {})
        assert mfa.get("passkey_login_enabled") is True
        assert "webauthn" in mfa.get("supported_types", [])
