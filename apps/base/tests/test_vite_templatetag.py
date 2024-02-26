from django.conf import settings
from django.test import override_settings

import pytest

from apps.base.templatetags.vite import vite_asset, vite_hmr_client
from apps.base.tests import BaseTest

VITE_MANIFEST_FILE = settings.BASE_DIR / "apps" / "base" / "tests" / "vite_manifest.json"
VITE_OUTPUT_DIR = "dist/"
VITE_SERVER_HOST = "example.com"
VITE_SERVER_PORT = "9999"
STATIC_URL = "/static/"


@override_settings(VITE_DEV_MODE=False, VITE_MANIFEST_FILE=settings.BASE_DIR / "vite_manifest.json")
class TestViteAssetNoManifestFile(BaseTest):
    def test_manifest_file_does_not_exist(self):
        with pytest.raises(FileNotFoundError, match="No such file or directory"):
            vite_asset("js/main.js")


@override_settings(VITE_DEV_MODE=True, VITE_MANIFEST_FILE=VITE_MANIFEST_FILE)
class TestViteAssetDevModeOn(BaseTest):
    def test_js_asset(self):
        result = vite_asset("js/main.js")
        assert result == '<script type="module" src="http://localhost:3000/public/static/js/main.js"></script>'

        with override_settings(
            VITE_SERVER_HOST=VITE_SERVER_HOST, VITE_SERVER_PORT=VITE_SERVER_PORT, STATIC_URL=STATIC_URL
        ):
            result = vite_asset("js/main.js")
            assert result == '<script type="module" src="http://example.com:9999/static/js/main.js"></script>'

    def test_css_asset(self):
        result = vite_asset("js/main.css")
        assert result == ""


@override_settings(VITE_DEV_MODE=False, VITE_MANIFEST_FILE=VITE_MANIFEST_FILE)
class TestViteAssetDevModeOff(BaseTest):
    def test_no_js_item(self):
        with pytest.raises(
            Exception,
            match=f'The vite asset "js/does_not_exist.js" was not found in the manifest file '
            f"{settings.BASE_DIR}/apps/base/tests/vite_manifest.json.",
        ):
            vite_asset("js/does_not_exist.js")

    def test_no_css_item(self):
        with pytest.raises(
            Exception,
            match=f'The vite asset "js/does_not_exist.css" was not found in the manifest file '
            f"{settings.BASE_DIR}/apps/base/tests/vite_manifest.json.",
        ):
            vite_asset("js/does_not_exist.css")

    def test_js_asset(self):
        result = vite_asset("js/main.js")
        assert result == '<script type="module" src="/public/static/dist/js/main-hashgoeshere.js"></script>'

        with override_settings(STATIC_URL=STATIC_URL, VITE_OUTPUT_DIR=VITE_OUTPUT_DIR):
            result = vite_asset("js/main.js")
            assert result == '<script type="module" src="/static/dist/main-hashgoeshere.js"></script>'

        with pytest.raises(
            Exception,
            match=f'The vite asset "js/does_not_exist.js" was not found in the manifest file '
            f"{settings.BASE_DIR}/apps/base/tests/vite_manifest.json.",
        ):
            vite_asset("js/does_not_exist.js")

    def test_css_asset(self):
        result = vite_asset("js/main.css")
        assert result == '<link rel="stylesheet" href="/public/static/dist/js/main-hashgoeshere.css">'

        with override_settings(STATIC_URL=STATIC_URL, VITE_OUTPUT_DIR=VITE_OUTPUT_DIR):
            result = vite_asset("js/main.css")
            assert result == '<link rel="stylesheet" href="/static/dist/main-hashgoeshere.css">'

        with pytest.raises(
            Exception,
            match=f'The vite asset "js/does_not_exist.css" was not found in the manifest file '
            f"{settings.BASE_DIR}/apps/base/tests/vite_manifest.json.",
        ):
            vite_asset("js/does_not_exist.css")


class TestViteHMRClientTagOn(BaseTest):
    @override_settings(VITE_DEV_MODE=True)
    def test_vite_hmr_client_dev_mode_on(self):
        result = vite_hmr_client()
        assert result == '<script type="module" src="http://localhost:3000/public/static/@vite/client"></script>'

        with override_settings(
            VITE_SERVER_HOST=VITE_SERVER_HOST, VITE_SERVER_PORT=VITE_SERVER_PORT, STATIC_URL=STATIC_URL
        ):
            result = vite_hmr_client()
            assert result == '<script type="module" src="http://example.com:9999/static/@vite/client"></script>'

    @override_settings(VITE_DEV_MODE=False)
    def test_vite_hmr_client_dev_mode_off(self):
        result = vite_hmr_client()
        assert result == ""
