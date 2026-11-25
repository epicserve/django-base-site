from typing import ClassVar

from django.conf import settings
from django.test import override_settings

import pytest

from apps.base.templatetags.vite import _get_manifest, vite_asset, vite_hmr_client

VITE_MANIFEST_FILE = settings.BASE_DIR / "apps" / "base" / "tests" / "vite_manifest.json"
VITE_OUTPUT_DIR = "dist/"
VITE_SERVER_HOST = "example.com"
VITE_SERVER_PORT = "9999"
STATIC_URL = "/static/"


class ViteTest:
    """Applies the class's `overrides` to the settings, and reads the manifest afresh in each test."""

    overrides: ClassVar[dict] = {}

    @pytest.fixture(autouse=True)
    def _settings(self, settings):
        for name, value in self.overrides.items():
            setattr(settings, name, value)
        # The manifest is cached for the process, which would keep the file one test read for the next.
        _get_manifest.cache_clear()
        yield
        _get_manifest.cache_clear()


class TestViteAssetNoManifestFile(ViteTest):
    overrides: ClassVar[dict] = {"VITE_DEV_MODE": False, "VITE_MANIFEST_FILE": settings.BASE_DIR / "vite_manifest.json"}

    def test_manifest_file_does_not_exist(self):
        with pytest.raises(FileNotFoundError, match="No such file or directory"):
            vite_asset("js/main.js")


class TestViteAssetDevModeOn(ViteTest):
    overrides: ClassVar[dict] = {"VITE_DEV_MODE": True, "VITE_MANIFEST_FILE": VITE_MANIFEST_FILE}

    def test_js_asset(self):
        result = vite_asset("js/main.js")
        assert result == '<script type="module" src="http://localhost:3000/public/static/dist/js/js/main.js"></script>'

        with override_settings(
            VITE_SERVER_HOST=VITE_SERVER_HOST,
            VITE_SERVER_PORT=VITE_SERVER_PORT,
            STATIC_URL=STATIC_URL,
            VITE_OUTPUT_DIR=VITE_OUTPUT_DIR,
        ):
            result = vite_asset("js/main.js")
            assert result == '<script type="module" src="http://example.com:9999/static/dist/js/main.js"></script>'

    def test_css_asset(self):
        result = vite_asset("js/main.css")
        assert result == ""


class TestViteAssetDevModeOff(ViteTest):
    overrides: ClassVar[dict] = {"VITE_DEV_MODE": False, "VITE_MANIFEST_FILE": VITE_MANIFEST_FILE}

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
        # A built entry's CSS is a separate file that no script loads, so the tag links it.
        result = vite_asset("js/main.js")
        assert result == (
            '<link rel="stylesheet" href="/public/static/dist/js/main-hashgoeshere.css">'
            '<script type="module" src="/public/static/dist/js/main-hashgoeshere.js"></script>'
        )

        with override_settings(STATIC_URL=STATIC_URL, VITE_OUTPUT_DIR=VITE_OUTPUT_DIR):
            result = vite_asset("js/main.js")
            assert result == (
                '<link rel="stylesheet" href="/static/dist/main-hashgoeshere.css">'
                '<script type="module" src="/static/dist/main-hashgoeshere.js"></script>'
            )

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

    def test_js_asset_links_the_css_of_the_chunks_it_imports(self):
        # js/admin.js imports _shared.js, which imports _base.js (and itself); each CSS file is linked once.
        # _lazy.js is a dynamic import, which loads its own CSS.
        result = vite_asset("js/admin.js")
        assert result == (
            '<link rel="stylesheet" href="/public/static/dist/js/admin-hash.css">'
            '<link rel="stylesheet" href="/public/static/dist/js/shared-hash.css">'
            '<link rel="stylesheet" href="/public/static/dist/js/base-hash.css">'
            '<script type="module" src="/public/static/dist/js/admin-hash.js"></script>'
        )


class TestViteHMRClientTagOn(ViteTest):
    @override_settings(VITE_DEV_MODE=True)
    def test_vite_hmr_client_dev_mode_on(self):
        result = vite_hmr_client()
        assert (
            result == '<script type="module" src="http://localhost:3000/public/static/dist/js/@vite/client"></script>'
        )

        with override_settings(
            VITE_SERVER_HOST=VITE_SERVER_HOST,
            VITE_SERVER_PORT=VITE_SERVER_PORT,
            STATIC_URL=STATIC_URL,
            VITE_OUTPUT_DIR=VITE_OUTPUT_DIR,
        ):
            result = vite_hmr_client()
            assert result == '<script type="module" src="http://example.com:9999/static/dist/@vite/client"></script>'

    @override_settings(VITE_DEV_MODE=False)
    def test_vite_hmr_client_dev_mode_off(self):
        result = vite_hmr_client()
        assert result == ""
