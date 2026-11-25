import importlib

from django.conf import settings
from django.test import override_settings
from django.urls import clear_url_caches

import pytest

import config.urls
from apps.accounts.tests.recipes import make_user
from apps.base.debug_toolbar import ENABLED_COOKIE, show_toolbar
from apps.base.tests import BaseTest
from apps.base.tests.sign_in import sign_in


@pytest.fixture()
def local_request(rf, settings):
    settings.DEBUG = True
    settings.INTERNAL_IPS = ["127.0.0.1"]
    return rf.get("/", REMOTE_ADDR="127.0.0.1")


class TestShowToolbar:
    def test_hidden_until_turned_on(self, local_request):
        assert show_toolbar(local_request) is False

    def test_shown_when_turned_on(self, local_request):
        local_request.COOKIES[ENABLED_COOKIE] = "1"

        assert show_toolbar(local_request) is True

    def test_hidden_when_turned_off(self, local_request):
        local_request.COOKIES[ENABLED_COOKIE] = "0"

        assert show_toolbar(local_request) is False

    def test_still_needs_debug(self, local_request, settings):
        settings.DEBUG = False
        local_request.COOKIES[ENABLED_COOKIE] = "1"

        assert show_toolbar(local_request) is False

    def test_still_needs_an_internal_ip(self, local_request, settings):
        settings.INTERNAL_IPS = ["10.0.0.1"]
        local_request.COOKIES[ENABLED_COOKIE] = "1"

        assert show_toolbar(local_request) is False


class TestAppContextDebugFlag(BaseTest):
    @classmethod
    def setUpTestData(cls):
        cls.jim = make_user("jim@example.com")

    def setUp(self):
        sign_in(self.client, self.jim)

    @override_settings(DEBUG=True)
    def test_reports_debug_on(self):
        assert self.client.get("/api/app-context/").json()["debug"] is True

    @override_settings(DEBUG=False)
    def test_reports_debug_off(self):
        assert self.client.get("/api/app-context/").json()["debug"] is False


class TestToolbarUrls:
    """
    The toolbar's URLs come with its app, which the settings install only when DEBUG is on at startup.

    They used to come with DEBUG itself, so a test that turned DEBUG on (test_seed) and was the first to load the
    URLconf imported the toolbar without its app installed, and every request failed.
    """

    @pytest.fixture(autouse=True)
    def _reload_urls_after(self):
        yield
        clear_url_caches()
        importlib.reload(config.urls)

    def _patterns(self) -> list[str]:
        clear_url_caches()
        return [str(pattern.pattern) for pattern in importlib.reload(config.urls).urlpatterns]

    def test_left_out_while_the_app_isnt_installed(self):
        apps = [app for app in settings.INSTALLED_APPS if app != "debug_toolbar"]
        with override_settings(DEBUG=True, INSTALLED_APPS=apps):
            patterns = self._patterns()

        assert "__debug__/" not in patterns
        assert "admin/doc/" in patterns
