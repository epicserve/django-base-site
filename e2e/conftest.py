import os

import pytest

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

# Headless Chromium 147 (Playwright 1.59) adds these two names to its own environment with setenv(), FC_FONTATIONS
# after its threads have started. On glibc before 2.41 (the dev image's Debian 12 has 2.36), the second new name makes
# setenv() move the environment to a bigger array and free the old one while another thread's getenv() can still be
# reading it, and the browser segfaulted in 36 of 2,000 launches in a stress test. Chromium 156 (Playwright 1.64.1)
# sets FC_FONTATIONS before its threads start, and none of 2,000 launches crashed without these lines. They stay for a
# stack still on an image with the older Chromium: when the names are already set, setenv() overwrites them in place.
# Playwright hands this process's environment to the browser. The values are the ones Chromium sets.
os.environ.setdefault("FC_FONTATIONS", "1")
os.environ.setdefault("DBUS_SESSION_BUS_ADDRESS", "disabled:")


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    return {**browser_type_launch_args, "args": ["--no-sandbox"]}


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    from apps.accounts.models import User

    # The e2e users keep User.timezone's default. In any other timezone (CI and the dev image run in UTC), the browser
    # gets TimezoneDetectModal on every signed-in page, and its backdrop takes every click.
    return {**browser_context_args, "timezone_id": User().timezone}


# The password every e2e user signs in with through the form.
PASSWORD = "dundermifflin"  # noqa: S105


@pytest.fixture()
def user(db):
    from apps.accounts.recipes import make_user

    return make_user("michael.scott@dundermifflin.com", password=PASSWORD, first_name="Michael", last_name="Scott")


@pytest.fixture()
def org(user):
    """Dunder Mifflin, owned by `user`, as their primary organization."""
    from apps.organizations.recipes import make_org

    return make_org(user, name="Dunder Mifflin", slug="dunder-mifflin")


@pytest.fixture()
def sign_in(page, live_server):
    """
    Sign the browser in as a user without the sign-in form, then open `path` and return its response.

    Use it in every test that isn't about signing in. It builds the session in this process with
    `apps.base.tests.sign_in.sign_in` (the user's primary organization selected unless `org` is given) and hands the
    browser its cookie, so the first page the browser loads is the one under test.
    """
    from django.conf import settings
    from django.test import Client

    from apps.base.tests.sign_in import sign_in as sign_in_client

    def _sign_in(user, path: str, *, org=None):
        client = sign_in_client(Client(), user, org)
        cookie = client.cookies[settings.SESSION_COOKIE_NAME].value
        page.context.add_cookies([{"name": settings.SESSION_COOKIE_NAME, "value": cookie, "url": live_server.url}])
        return page.goto(f"{live_server.url}{path}")

    return _sign_in
