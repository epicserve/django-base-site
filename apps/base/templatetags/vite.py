import json
from functools import lru_cache
from typing import TypeVar

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

T = TypeVar("T")

register = template.Library()


class ViteSettings:
    """Object to allow settings to be overridden in tests."""

    def _get_setting(self, var_name: str, default: T) -> T:
        return getattr(settings, var_name, default)

    @property
    def VITE_DEV_MODE(self):
        return self._get_setting("VITE_DEV_MODE", settings.DEBUG)

    @property
    def VITE_OUTPUT_DIR(self):
        return self._get_setting("VITE_OUTPUT_DIR", "dist/js/")

    @property
    def VITE_MANIFEST_FILE(self):
        return self._get_setting(
            "VITE_MANIFEST_FILE", settings.STATIC_ROOT.joinpath(self.VITE_OUTPUT_DIR, ".vite", "manifest.json")
        )

    @property
    def VITE_SERVER_HOST(self):
        return self._get_setting("VITE_SERVER_HOST", "localhost")

    @property
    def VITE_SERVER_PORT(self):
        return self._get_setting("VITE_SERVER_PORT", "3000")


vite_settings = ViteSettings()


def _get_css_link(filename: str) -> str:
    base_url = f"{settings.STATIC_URL}{vite_settings.VITE_OUTPUT_DIR}"
    return mark_safe(f'<link rel="stylesheet" href="{base_url}{filename}">')  # noqa: S308


def _get_script_tag(filename: str) -> str:
    if vite_settings.VITE_DEV_MODE is False:
        base_url = f"{settings.STATIC_URL}{vite_settings.VITE_OUTPUT_DIR}"
    else:
        base_url = f"http://{vite_settings.VITE_SERVER_HOST}:{vite_settings.VITE_SERVER_PORT}{settings.STATIC_URL}"
    return mark_safe(f'<script type="module" src="{base_url}{filename}"></script>')  # noqa: S308


@lru_cache
def _get_manifest():
    with open(vite_settings.VITE_MANIFEST_FILE) as f:
        content = f.read()
        manifest = json.loads(content)
        return manifest


def _get_file_data(filename: str) -> dict[str, str | list[str | None] | bool]:
    manifest = _get_manifest()
    js_filename = filename.replace(".css", ".js") if filename.endswith(".css") else filename
    file_data = manifest.get(js_filename)
    if file_data is None:
        raise Exception(
            f'The vite asset "{filename}" was not found in the manifest file {vite_settings.VITE_MANIFEST_FILE}.'
        )
    return file_data


def _get_css_asset(filename: str):
    if vite_settings.VITE_DEV_MODE is True:
        return ""
    file_data = _get_file_data(filename)
    hashed_filename = file_data.get("css", [None])[0]  # type: ignore
    return _get_css_link(hashed_filename)  # type: ignore


def _get_js_asset(filename: str):
    if vite_settings.VITE_DEV_MODE is True:
        return _get_script_tag(filename)
    file_data = _get_file_data(filename)
    hashed_filename = file_data.get("file")
    return _get_script_tag(hashed_filename)  # type: ignore


@register.simple_tag
def vite_asset(filename: str):
    if str(filename).endswith("css") is True:
        return _get_css_asset(filename)
    return _get_js_asset(filename)


@register.simple_tag
def vite_hmr_client() -> str:
    if vite_settings.VITE_DEV_MODE is False:
        return ""
    return _get_script_tag("@vite/client")
