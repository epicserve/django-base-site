"""Errors go to Sentry when SENTRY_DSN is set, without users' personal details, and nothing is sent when it's blank."""

import importlib
import sys

from django.apps import apps as django_apps
from django.core.handlers.wsgi import WSGIHandler
from django.core.signals import request_finished, request_started
from django.db import close_old_connections
from django.test import Client, RequestFactory
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

import pytest
import sentry_sdk
from model_bakery import baker
from sentry_sdk.transport import Transport

import config.settings._base
from apps.accounts.models import User
from apps.base.sentry import init_sentry


@csrf_exempt
def out_of_paper(request):
    raise RuntimeError("Dunder Mifflin is out of paper")


urlpatterns = [path("out-of-paper/", out_of_paper)]


class RecordingTransport(Transport):
    """Keeps the events Sentry would send, instead of sending them."""

    def __init__(self):
        super().__init__()
        self.events: list[dict] = []

    def capture_envelope(self, envelope):
        if event := envelope.get_event():
            self.events.append(event)


def _post_through_wsgi(url: str, data: dict, **environ: str) -> str:
    """
    Send a JSON POST through WSGIHandler, as gunicorn does, and return its status.

    The test client skips the part of Sentry that adds the request to an event. Like the test client, this keeps
    Django from closing the database connection, which would end the test's transaction.
    """
    statuses = []
    request_started.disconnect(close_old_connections)
    request_finished.disconnect(close_old_connections)
    try:
        response = WSGIHandler()(
            RequestFactory().post(url, data=data, content_type="application/json", **environ).environ,
            lambda status, headers, exc_info=None: statuses.append(status),
        )
        response.close()
    finally:
        request_started.connect(close_old_connections)
        request_finished.connect(close_old_connections)
    return statuses[0]


@pytest.fixture()
def sent_events(settings, monkeypatch):
    """Set SENTRY_DSN, and keep what Sentry would send in the returned list."""
    transport = RecordingTransport()
    real_init = sentry_sdk.init
    monkeypatch.setattr(sentry_sdk, "init", lambda **options: real_init(**options, transport=transport))
    settings.SENTRY_DSN = "https://public@sentry.example.invalid/1"
    yield transport.events
    sentry_sdk.get_client().close()
    sentry_sdk.get_global_scope().set_client(None)


class TestTurnedOff:
    def test_a_blank_dsn_starts_nothing(self, settings, monkeypatch):
        calls = []
        monkeypatch.setattr(sentry_sdk, "init", lambda **options: calls.append(options))
        settings.SENTRY_DSN = ""

        init_sentry()

        assert calls == []

    @pytest.mark.parametrize("module", ["test_runner", "e2e", "api_types", "deploy_check"])
    def test_test_and_tool_settings_turn_it_off(self, module, monkeypatch):
        # As if .env set it. Each of these settings modules starts with `from ._base import *`.
        monkeypatch.setattr(config.settings._base, "SENTRY_DSN", "https://public@sentry.example.invalid/1")
        name = f"config.settings.{module}"
        monkeypatch.delitem(sys.modules, name, raising=False)

        assert importlib.import_module(name).SENTRY_DSN == ""


class TestStartsWithDjango:
    def test_the_base_app_starts_it_once_django_is_set_up(self, monkeypatch):
        calls = []
        monkeypatch.setattr("apps.base.sentry.init_sentry", lambda: calls.append("init_sentry"))

        django_apps.get_app_config("base").ready()

        assert calls == ["init_sentry"]


@pytest.mark.django_db
@pytest.mark.urls(__name__)
class TestTurnedOn:
    def test_reports_from_django_and_celery(self, sent_events):
        init_sentry()

        assert {"django", "celery"} <= set(sentry_sdk.get_client().integrations)

    def test_an_error_in_a_view_is_reported_without_personal_details(self, sent_events, settings):
        init_sentry()
        client = Client()
        client.force_login(baker.make(User, email="michael.scott@dundermifflin.com"))
        session_key = client.session.session_key

        status = _post_through_wsgi(
            "/out-of-paper/",
            {"invitee_email": "jim.halpert@dundermifflin.com"},
            REMOTE_ADDR="203.0.113.7",
            # As a proxy in front of the app would add it.
            HTTP_X_FORWARDED_FOR="198.51.100.4",
            HTTP_COOKIE=f"{settings.SESSION_COOKIE_NAME}={session_key}",
        )

        assert status == "500 Internal Server Error"
        (event,) = sent_events
        assert event["exception"]["values"][-1]["value"] == "Dunder Mifflin is out of paper"
        assert event["environment"] == settings.INSTANCE
        assert event["request"]["url"] == "http://testserver/out-of-paper/"
        assert event["request"]["headers"]["Cookie"] == "[Filtered]"
        assert "user" not in event
        # Sentry empties the body and notes in `_meta` that its configuration removed it.
        assert event["request"]["data"] == ""
        for personal in [
            session_key,
            "203.0.113.7",
            "198.51.100.4",
            "michael.scott@dundermifflin.com",
            "jim.halpert@dundermifflin.com",
        ]:
            assert personal not in str(event)
