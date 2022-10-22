import json
from functools import lru_cache

from django import template
from django.conf import settings

register = template.Library()

MANIFEST_FILE = settings.PUBLIC_STATIC.joinpath("dist", "js", "manifest.json")


@lru_cache
def get_manifest():

    with open(MANIFEST_FILE) as f:
        content = f.read()
        manifest = json.loads(content)
        return manifest


@register.simple_tag
def vite_asset(filename):

    manifest = get_manifest()
    file_data = manifest.get(filename)
    if file_data is None:
        raise Exception(f'The vite asset "{filename}" was not found in the manifest file {MANIFEST_FILE}.')

    return f"{settings.STATIC_URL}dist/js/{file_data['file']}"
