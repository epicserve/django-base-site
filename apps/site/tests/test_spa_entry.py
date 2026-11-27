"""The SPA's entry module is named in three places that have to agree."""

import json

from django.conf import settings

import pytest

from apps.base.templatetags.vite import _get_manifest
from apps.site.api import _get_app_version

# The entry's path under frontend/, which is also its key in Vite's manifest.
SPA_ENTRY = "js/app.ts"


class TestSpaEntry:
    def test_vite_builds_the_entry(self):
        vite_config = (settings.BASE_DIR / "frontend" / "config" / "vite.config.mjs").read_text()
        assert f"app: resolve(import.meta.dirname, '../{SPA_ENTRY}')" in vite_config
        assert (settings.BASE_DIR / "frontend" / SPA_ENTRY).is_file()

    def test_spa_shell_loads_the_entry(self):
        template = (settings.BASE_DIR / "apps" / "base" / "templates" / "layouts" / "spa_shell.html").read_text()
        assert f"{{% vite_asset '{SPA_ENTRY}' %}}" in template


class TestAppVersion:
    """`/api/version/` reports the entry's hashed filename, which the SPA polls to offer a reload after a deploy."""

    @pytest.fixture(autouse=True)
    def _manifest(self, settings, tmp_path):
        manifest = tmp_path / "manifest.json"
        manifest.write_text(json.dumps({SPA_ENTRY: {"file": "app-abc123.js", "isEntry": True, "src": SPA_ENTRY}}))
        settings.VITE_DEV_MODE = False
        settings.VITE_MANIFEST_FILE = manifest
        _get_manifest.cache_clear()
        yield
        _get_manifest.cache_clear()

    def test_reads_the_entry_from_the_manifest(self):
        assert _get_app_version() == "app-abc123.js"
