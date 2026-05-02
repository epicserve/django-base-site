"""Tests for the `spa_url` template tag and the SPA_URLS registry."""

from django.conf import settings
from django.template import Context, Template

import pytest


def render(template_str: str, context: dict | None = None) -> str:
    return Template(template_str).render(Context(context or {}))


class TestSpaUrlTag:
    def test_resolves_static_route(self):
        rendered = render("{% load spa %}{% spa_url 'org-switch' %}")
        assert rendered == "/organizations/switch/"

    def test_formats_slug_into_path(self):
        rendered = render("{% load spa %}{% spa_url 'org-settings-general' slug='acme' %}")
        assert rendered == "/organizations/acme/settings/general/"

    def test_each_settings_tab_url_is_registered(self):
        # Settings tabs need a registered SPA URL so legacy Django templates
        # (and any direct-link emails) can target them via {% spa_url %}.
        expected = {
            "org-settings-general": "/organizations/{slug}/settings/general/",
            "org-settings-members": "/organizations/{slug}/settings/members/",
            "org-settings-teams": "/organizations/{slug}/settings/teams/",
        }
        for name, path in expected.items():
            assert settings.SPA_URLS[name] == path

    def test_unknown_route_raises(self):
        with pytest.raises(KeyError):
            render("{% load spa %}{% spa_url 'definitely-not-a-route' %}")
