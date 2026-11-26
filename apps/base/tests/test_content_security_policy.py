"""
Every response carries an enforced Content-Security-Policy, and the SPA shell's inline script carries its nonce.

Browsers block anything the policy doesn't allow. `e2e/test_content_security_policy.py` loads the pages in a browser
and fails on any violation.
"""

import re
import runpy

from django.conf import settings
from django.test import Client
from django.utils.csp import CSP

import pytest

BASE_SETTINGS = settings.BASE_DIR / "config" / "settings" / "_base.py"

# Read from the environment, which the web container gets from .env.
ENVIRONMENT = [
    "DEBUG",
    "VITE_DEV_MODE",
    "HOST_PORT_VITE",
    "DEFAULT_FILE_STORAGE",
    "MEDIA_S3_ENDPOINT_URL",
    "MEDIA_S3_URL_ENDPOINT_URL",
    "MEDIA_S3_BUCKET_NAME",
    "STATICFILES_STORAGE",
    "AWS_STORAGE_BUCKET_NAME",
    "AWS_S3_REGION",
]


@pytest.fixture()
def policy_for(monkeypatch):
    """Run config/settings/_base.py afresh under the given environment, without .env, and return its policy."""

    def load(**environ: str) -> dict[str, list[str]]:
        monkeypatch.setenv("READ_DOT_ENV_FILE", "off")
        monkeypatch.setenv("SECRET_KEY", "secret-key-for-testing-only")
        for name in ENVIRONMENT:
            monkeypatch.delenv(name, raising=False)
        for name, value in environ.items():
            monkeypatch.setenv(name, value)
        return runpy.run_path(str(BASE_SETTINGS))["SECURE_CSP"]

    return load


class TestTheHeader:
    def test_the_spa_shell_enforces_the_policy(self):
        response = Client().get("/accounts/login/")

        assert CSP.HEADER_ENFORCE in response
        assert CSP.HEADER_REPORT_ONLY not in response

    def test_the_theme_script_carries_the_policys_nonce(self):
        response = Client().get("/accounts/login/")

        (nonce,) = re.findall(r'<script nonce="([^"]+)">', response.content.decode())
        script_src = next(
            directive for directive in response[CSP.HEADER_ENFORCE].split("; ") if directive.startswith("script-src ")
        )
        assert f"'nonce-{nonce}'" in script_src.split()

    def test_each_response_has_its_own_nonce(self):
        client = Client()

        first, second = (client.get("/accounts/login/")[CSP.HEADER_ENFORCE] for _ in range(2))

        assert first != second


class TestThePolicy:
    def test_built_assets_need_nothing_inline_but_the_nonced_script(self, policy_for):
        policy = policy_for(DEBUG="off")

        assert policy["script-src"] == [CSP.SELF, CSP.NONCE]
        assert all(CSP.UNSAFE_INLINE not in values and CSP.UNSAFE_EVAL not in values for values in policy.values())
        assert not any("localhost" in value for values in policy.values() for value in values)

    def test_the_vite_dev_server_is_allowed_in_development(self, policy_for):
        policy = policy_for(DEBUG="on", HOST_PORT_VITE="3011")

        assert "http://localhost:3011" in policy["script-src"]
        assert policy["style-src"][-2:] == ["http://localhost:3011", CSP.UNSAFE_INLINE]
        assert policy["connect-src"] == [CSP.SELF, "http://localhost:3011", "ws://localhost:3011"]

    def test_images_load_from_the_browser_facing_media_endpoint(self, policy_for):
        policy = policy_for(
            DEBUG="off",
            DEFAULT_FILE_STORAGE="storages.backends.s3boto3.S3Boto3Storage",
            MEDIA_S3_ENDPOINT_URL="http://silo:9000",
            MEDIA_S3_URL_ENDPOINT_URL="http://localhost:9022",
        )

        assert policy["img-src"] == [CSP.SELF, "data:", "http://localhost:9022"]

    def test_images_load_from_the_s3_bucket_without_an_endpoint(self, policy_for):
        policy = policy_for(
            DEBUG="off",
            DEFAULT_FILE_STORAGE="storages.backends.s3boto3.S3Boto3Storage",
            MEDIA_S3_BUCKET_NAME="dunder-mifflin-media",
        )

        assert policy["img-src"][-1] == "https://dunder-mifflin-media.s3.amazonaws.com"

    def test_media_on_disk_comes_from_this_site(self, policy_for):
        policy = policy_for(DEBUG="off", DEFAULT_FILE_STORAGE="django.core.files.storage.FileSystemStorage")

        assert policy["img-src"] == [CSP.SELF, "data:"]

    def test_static_files_on_s3_are_allowed_by_their_bucket_path_not_the_shared_host(self, policy_for):
        policy = policy_for(
            DEBUG="off",
            DEFAULT_FILE_STORAGE="apps.base.storage.MediaS3Storage",
            STATICFILES_STORAGE="apps.base.storage.MediaS3Storage",
            AWS_STORAGE_BUCKET_NAME="dunder-mifflin",
            AWS_S3_REGION="us-east-2",
        )

        static = "https://s3.us-east-2.amazonaws.com/dunder-mifflin/static/"
        assert policy["script-src"] == [CSP.SELF, CSP.NONCE, static]
        assert policy["img-src"][-1] == "https://s3.us-east-2.amazonaws.com/dunder-mifflin/media/"
        assert "https://s3.us-east-2.amazonaws.com" not in [value for values in policy.values() for value in values]
