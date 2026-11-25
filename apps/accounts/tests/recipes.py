"""Test data for accounts. Build users with these instead of `User.objects.create_user` or `baker.make(User)`."""

from itertools import count

from allauth.account.models import EmailAddress
from allauth.mfa.recovery_codes.internal.auth import RecoveryCodes
from allauth.mfa.totp.internal.auth import TOTP, generate_totp_secret

from apps.accounts.models import User

# Every recipe user gets this password unless the test passes another one. The test settings hash with MD5, so setting
# it is cheap.
TEST_PASSWORD = "test-password"  # noqa: S105

_numbers = count(1)


def make_user(email: str | None = None, *, password: str = TEST_PASSWORD, verified: bool = True, **fields) -> User:
    """
    Make a user who can sign in with `email` and `password`, with a primary `EmailAddress` for that email.

    The email doubles as the username unless `username` is passed. `verified=False` leaves the address unverified. Any
    other keyword sets a `User` field, such as `first_name` or `timezone`.
    """
    email = email or f"user{next(_numbers)}@example.com"
    fields.setdefault("username", email)
    user = User.objects.create_user(email=email, password=password, **fields)
    EmailAddress.objects.create(user=user, email=email, verified=verified, primary=True)
    return user


def make_superuser(email: str | None = None, **fields) -> User:
    """Make a staff superuser, otherwise like `make_user`."""
    return make_user(email, is_staff=True, is_superuser=True, **fields)


def make_totp(user: User, *, recovery_codes: bool = True) -> str:
    """
    Turn on two-factor authentication for `user` with an authenticator app, and return its TOTP secret.

    Setting it up in the app also makes recovery codes; `recovery_codes=False` leaves them out. Sign in with
    `current_totp_code(secret)` from `apps.accounts.tests.totp`.
    """
    secret = generate_totp_secret()
    TOTP.activate(user, secret)
    if recovery_codes:
        RecoveryCodes.activate(user)
    return secret
