import json
from functools import lru_cache

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()

VITE_OUTPUT_DIR = getattr(settings, "VITE_OUTPUT_DIR", "dist/js/")
VITE_MANIFEST_FILE = getattr(
    settings, "VITE_MANIFEST_FILE", settings.STATIC_ROOT.joinpath(VITE_OUTPUT_DIR, ".vite", "manifest.json")
)
VITE_DEV_MODE = getattr(settings, "VITE_DEV_MODE", settings.DEBUG)
VITE_SERVER_HOST = getattr(settings, "VITE_SERVER_HOST", "localhost")
VITE_SERVER_PORT = getattr(settings, "VITE_SERVER_PORT", "3000")


def get_css_link(file: str) -> str:
    base_url = f"{settings.STATIC_URL}{VITE_OUTPUT_DIR}"
    return mark_safe(f'<link rel="stylesheet" href="{base_url}{file}">')  # nosec B308, B703


def get_script(file: str) -> str:
    if VITE_DEV_MODE is False:
        base_url = f"{settings.STATIC_URL}{VITE_OUTPUT_DIR}"
    else:
        base_url = f"http://{VITE_SERVER_HOST}:{VITE_SERVER_PORT}{settings.STATIC_URL}"
    return mark_safe(f'<script type="module" src="{base_url}{file}"></script>')  # nosec B308, B703


@lru_cache
def get_manifest():
    with open(VITE_MANIFEST_FILE) as f:
        content = f.read()
        manifest = json.loads(content)
        return manifest


@register.simple_tag
def vite_asset(filename: str):
    is_css = str(filename).endswith("css")
    if VITE_DEV_MODE is True:
        if is_css is True:
            return ""
        return get_script(filename)

    manifest = get_manifest()
    if is_css is True:
        filename = filename.replace(".css", ".js")
        file_data = manifest.get(filename)
    else:
        file_data = manifest.get(filename)

    if file_data is None:
        raise Exception(f'The vite asset "{filename}" was not found in the manifest file {VITE_MANIFEST_FILE}.')

    if is_css is True:
        filename = file_data.get("css", [None])[0]
        if filename is None:
            raise Exception(f'The vite asset "{filename}" was not found in the manifest file {VITE_MANIFEST_FILE}.')
        return get_css_link(filename)
    return get_script(filename)


@register.simple_tag
def vite_hmr_client():
    if VITE_DEV_MODE is False:
        return ""
    return get_script("@vite/client")
