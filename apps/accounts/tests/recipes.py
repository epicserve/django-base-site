"""
Test data for accounts. Build users with these instead of `User.objects.create_user` or `baker.make(User)`.

`make_user` and `make_superuser` live in `apps.accounts.recipes`, because `manage.py seed` uses them too.
"""

from allauth.mfa.recovery_codes.internal.auth import RecoveryCodes
from allauth.mfa.totp.internal.auth import TOTP, generate_totp_secret

from apps.accounts.models import User
from apps.accounts.recipes import TEST_PASSWORD, make_superuser, make_user

__all__ = ["TEST_PASSWORD", "make_superuser", "make_totp", "make_user"]


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
