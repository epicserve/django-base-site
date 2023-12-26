import json
from functools import lru_cache
from typing import TypeVar

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

T = TypeVar("T")

register = template.Library()

"""Object to allow settings to be overridden in tests"""


class ViteSettings(object):
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


def get_css_link(file: str) -> str:
    base_url = f"{settings.STATIC_URL}{vite_settings.VITE_OUTPUT_DIR}"
    return mark_safe(f'<link rel="stylesheet" href="{base_url}{file}">')  # nosec B308, B703


def get_script(file: str) -> str:
    if vite_settings.VITE_DEV_MODE is False:
        base_url = f"{settings.STATIC_URL}{vite_settings.VITE_OUTPUT_DIR}"
    else:
        base_url = f"http://{vite_settings.VITE_SERVER_HOST}:{vite_settings.VITE_SERVER_PORT}{settings.STATIC_URL}"
    return mark_safe(f'<script type="module" src="{base_url}{file}"></script>')  # nosec B308, B703


@lru_cache
def get_manifest():
    with open(vite_settings.VITE_MANIFEST_FILE) as f:
        content = f.read()
        manifest = json.loads(content)
        return manifest


@register.simple_tag
def vite_asset(filename: str):
    is_css = str(filename).endswith("css")
    if vite_settings.VITE_DEV_MODE is True:
        if is_css is True:
            return ""
        return get_script(filename)

    manifest = get_manifest()
    if is_css is True:
        js_filename = filename.replace(".css", ".js")
        file_data = manifest.get(js_filename)
    else:
        file_data = manifest.get(filename)

    if file_data is None:
        raise Exception(
            f'The vite asset "{filename}" was not found in the manifest file {vite_settings.VITE_MANIFEST_FILE}.'
        )

    hashed_filename = file_data.get("css", [None])[0] if is_css is True else file_data.get("file")

    if is_css is True:
        return get_css_link(hashed_filename)
    return get_script(hashed_filename)


@register.simple_tag
def vite_hmr_client() -> str:
    if vite_settings.VITE_DEV_MODE is False:
        return ""
    return get_script("@vite/client")
