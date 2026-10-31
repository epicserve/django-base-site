import pytest

from apps.accounts.models import User

APP_CONTEXT_URL = "/api/app-context/"
HIDE_URL = "/api/impersonation/hide-banner/"


@pytest.mark.django_db
class TestImpersonationBanner:
    @pytest.fixture(autouse=True)
    def _setup(self, client):
        self.client = client
        self.admin = User.objects.create_superuser(
            username="leslie",
            email="leslie@example.com",
            password="secret",  # noqa: S106
        )
        self.jim = User.objects.create_user(
            username="jim",
            email="jim@example.com",
            password="secret",  # noqa: S106
        )
        self.pam = User.objects.create_user(
            username="pam",
            email="pam@example.com",
            password="secret",  # noqa: S106
        )
        self.client.force_login(self.admin)

    def _impersonate(self, user):
        resp = self.client.post("/hijack/acquire/", {"user_pk": user.pk, "next": "/"})
        assert resp.status_code == 302

    def _stop_impersonating(self):
        resp = self.client.post("/hijack/release/", {"next": "/"})
        assert resp.status_code == 302

    def _context_user(self):
        resp = self.client.get(APP_CONTEXT_URL)
        assert resp.status_code == 200
        return resp.json()["user"]

    def test_banner_is_shown_when_impersonation_starts(self):
        self._impersonate(self.jim)

        user = self._context_user()
        assert user["id"] == self.jim.pk
        assert user["is_hijacked"] is True
        assert user["impersonation_banner_hidden"] is False

    def test_hide_keeps_banner_hidden_for_the_rest_of_the_impersonation(self):
        self._impersonate(self.jim)

        resp = self.client.post(HIDE_URL)

        assert resp.status_code == 204
        assert self._context_user()["impersonation_banner_hidden"] is True
        assert self._context_user()["impersonation_banner_hidden"] is True

    def test_hide_requires_an_impersonation(self):
        resp = self.client.post(HIDE_URL)

        assert resp.status_code == 403
        assert self._context_user()["impersonation_banner_hidden"] is False

    def test_impersonating_the_same_user_again_shows_banner(self):
        self._impersonate(self.jim)
        self.client.post(HIDE_URL)
        self._stop_impersonating()

        assert self._context_user()["impersonation_banner_hidden"] is False

        self._impersonate(self.jim)

        assert self._context_user()["impersonation_banner_hidden"] is False

    def test_impersonating_another_user_shows_banner(self):
        self._impersonate(self.jim)
        self.client.post(HIDE_URL)
        self._stop_impersonating()

        self._impersonate(self.pam)

        user = self._context_user()
        assert user["id"] == self.pam.pk
        assert user["impersonation_banner_hidden"] is False

    def test_hijack_notification_is_not_injected_into_the_spa_shell(self):
        self._impersonate(self.jim)

        resp = self.client.get("/")

        assert resp.status_code == 200
        assert b"djhj" not in resp.content
