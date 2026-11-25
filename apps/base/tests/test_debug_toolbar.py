from django.test import override_settings

import pytest

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
