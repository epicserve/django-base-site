"""
Build users. The tests use these (through `apps.accounts.tests.recipes`), and so does `manage.py seed`.

A recipe creates a new row unless it's given `update=True`, which looks the row up and brings it back to what the
recipe says instead, so the seed command can be rerun. Tests leave it off, so a test that builds the same row twice
fails rather than quietly changing a row another test shares.
"""

from functools import cache
from itertools import count

from django.conf import settings
from django.contrib.auth.hashers import make_password

from allauth.account.models import EmailAddress

from apps.accounts.models import User

# Every recipe user gets this password unless the caller passes another one. The test settings hash with MD5, so
# setting it is cheap.
TEST_PASSWORD = "test-password"  # noqa: S105

_numbers = count(1)


@cache
def _hash(password: str, hasher: str) -> str:
    # The default hasher is deliberately slow and the seed command makes dozens of users with one password, so hash
    # each password once per hasher. The users share a salt, which only matters for real passwords.
    return make_password(password)


def make_user(
    email: str | None = None, *, password: str = TEST_PASSWORD, verified: bool = True, update: bool = False, **fields
) -> User:
    """
    Make a user who can sign in with `email` and `password`, with a primary `EmailAddress` for that email.

    The email doubles as the username unless `username` is passed. `verified=False` leaves the address unverified. Any
    other keyword sets a `User` field, such as `first_name` or `timezone`. With `update=True`, an existing user with
    that username gets these values instead, and a new address is primary only when the user has no other primary one.
    """
    email = email or f"user{next(_numbers)}@example.com"
    username = fields.pop("username", email)
    fields |= {"email": email, "password": _hash(password, settings.PASSWORD_HASHERS[0])}
    if update:
        user, _ = User.objects.update_or_create(username=username, defaults=fields)
    else:
        user = User.objects.create(username=username, **fields)
    has_primary = EmailAddress.objects.filter(user=user, primary=True).exclude(email=email).exists()
    EmailAddress.objects.update_or_create(
        user=user,
        email=email,
        defaults={"verified": verified},
        create_defaults={"verified": verified, "primary": not has_primary},
    )
    return user


def make_superuser(email: str | None = None, **fields) -> User:
    """Make a staff superuser, otherwise like `make_user`."""
    return make_user(email, is_staff=True, is_superuser=True, **fields)
