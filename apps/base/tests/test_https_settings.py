"""The HTTPS settings are on by default outside DEBUG, and django-alive's health checks are never redirected."""

import runpy

from django.conf import settings
from django.urls import reverse

import pytest

BASE_SETTINGS = settings.BASE_DIR / "config" / "settings" / "_base.py"

HTTPS_VARIABLES = [
    "SECURE_SSL_REDIRECT",
    "SESSION_COOKIE_SECURE",
    "CSRF_COOKIE_SECURE",
    "SECURE_HSTS_SECONDS",
    "SECURE_HSTS_INCLUDE_SUBDOMAINS",
    "SECURE_HSTS_PRELOAD",
]


@pytest.fixture()
def load_base_settings(monkeypatch):
    """Run config/settings/_base.py afresh under the given environment, without .env, and return its settings."""

    def load(**environ: str) -> dict:
        # The settings are worked out from the environment on import, so the `settings` fixture can't test them.
        monkeypatch.setenv("READ_DOT_ENV_FILE", "off")
        monkeypatch.setenv("SECRET_KEY", "secret-key-for-testing-only")
        for name in HTTPS_VARIABLES:
            monkeypatch.delenv(name, raising=False)
        for name, value in environ.items():
            monkeypatch.setenv(name, value)
        # Run the file rather than the module: config.settings._base is already imported, and stays as it is.
        return runpy.run_path(str(BASE_SETTINGS))

    return load


class TestHttpsSettingDefaults:
    def test_on_when_debug_is_off(self, load_base_settings):
        base = load_base_settings(DEBUG="off")

        assert base["SECURE_SSL_REDIRECT"] is True
        assert base["SESSION_COOKIE_SECURE"] is True
        assert base["CSRF_COOKIE_SECURE"] is True
        assert base["SECURE_HSTS_SECONDS"] == 31_536_000
        # These reach every subdomain, so they stay off until a project turns them on for its own domain.
        assert base["SECURE_HSTS_INCLUDE_SUBDOMAINS"] is False
        assert base["SECURE_HSTS_PRELOAD"] is False

    def test_off_when_debug_is_on(self, load_base_settings):
        # Local dev runs over plain http://localhost, with nothing serving HTTPS to redirect to.
        base = load_base_settings(DEBUG="on")

        assert base["SECURE_SSL_REDIRECT"] is False
        assert base["SESSION_COOKIE_SECURE"] is False
        assert base["CSRF_COOKIE_SECURE"] is False
        assert base["SECURE_HSTS_SECONDS"] == 0
        assert base["SECURE_HSTS_INCLUDE_SUBDOMAINS"] is False
        assert base["SECURE_HSTS_PRELOAD"] is False

    def test_the_environment_overrides_the_defaults(self, load_base_settings):
        base = load_base_settings(
            DEBUG="off",
            SECURE_SSL_REDIRECT="off",
            SESSION_COOKIE_SECURE="off",
            CSRF_COOKIE_SECURE="off",
            SECURE_HSTS_SECONDS="3600",
            SECURE_HSTS_INCLUDE_SUBDOMAINS="on",
            SECURE_HSTS_PRELOAD="on",
        )

        assert base["SECURE_SSL_REDIRECT"] is False
        assert base["SESSION_COOKIE_SECURE"] is False
        assert base["CSRF_COOKIE_SECURE"] is False
        assert base["SECURE_HSTS_SECONDS"] == 3600
        assert base["SECURE_HSTS_INCLUDE_SUBDOMAINS"] is True
        assert base["SECURE_HSTS_PRELOAD"] is True


class TestSslRedirect:
    @pytest.fixture(autouse=True)
    def _redirect(self, settings):
        # The test settings turn the redirect off, so turn it back on, keeping _base.py's SECURE_REDIRECT_EXEMPT.
        settings.SECURE_SSL_REDIRECT = True

    def test_redirects_plain_http_to_https(self, client):
        response = client.get("/accounts/login/?next=/teams/")

        assert response.status_code == 301
        assert response["Location"] == "https://testserver/accounts/login/?next=/teams/"

    def test_leaves_the_alive_check_on_plain_http(self, client):
        # Load balancers and container probes call the health checks over plain HTTP, and would read a redirect as down.
        response = client.get(reverse("alive_alive"))

        assert response.status_code == 200

    @pytest.mark.django_db
    def test_leaves_the_health_check_on_plain_http(self, client):
        response = client.get(reverse("alive_health"))

        assert response.status_code == 200
