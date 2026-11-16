import os

import pytest
from model_bakery import baker

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


@pytest.fixture()
def user(db):
    from allauth.account.models import EmailAddress

    from apps.accounts.models import User

    user = baker.make(
        User,
        email="michael.scott@dundermifflin.com",
        first_name="Michael",
        last_name="Scott",
    )
    user.set_password("dundermifflin")
    user.save()
    EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)
    return user
