import pytest

from apps.accounts.models import User
from apps.base.debug_toolbar import ENABLED_COOKIE, show_toolbar


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


@pytest.mark.django_db
class TestAppContextDebugFlag:
    @pytest.fixture(autouse=True)
    def _login(self, client):
        client.force_login(User.objects.create_user(username="jim", password="secret"))  # noqa: S106
        self.client = client

    def test_reports_debug_on(self, settings):
        settings.DEBUG = True

        assert self.client.get("/api/app-context/").json()["debug"] is True

    def test_reports_debug_off(self, settings):
        settings.DEBUG = False

        assert self.client.get("/api/app-context/").json()["debug"] is False
