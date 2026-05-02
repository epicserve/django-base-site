import os

import pytest
from model_bakery import baker

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"


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
