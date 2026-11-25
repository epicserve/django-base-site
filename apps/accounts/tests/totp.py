"""TOTP codes for tests that sign in with an authenticator app."""

import time

import pyotp


def current_totp_code(secret: str, seconds_left: float = 5) -> str:
    """
    Return `secret`'s TOTP code, first waiting for the next 30-second window if this one ends within `seconds_left`.

    allauth accepts only the current window's code (`MFA_TOTP_TOLERANCE` is 0), so a code made just before a window
    ends is rejected if the server checks it in the next one. `pyotp.TOTP(secret).now()` failed that way now and then.
    """
    totp = pyotp.TOTP(secret)
    left = totp.interval - time.time() % totp.interval
    if left < seconds_left:
        time.sleep(left + 0.1)
    return totp.at(time.time())
