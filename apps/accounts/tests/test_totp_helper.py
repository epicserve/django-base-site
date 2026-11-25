"""`current_totp_code()` never makes a code in a window's last seconds, when it could expire before it's checked."""

import pyotp
import pytest

from apps.accounts.tests import totp
from apps.accounts.tests.totp import current_totp_code

SECRET = pyotp.random_base32()
# The start of a 30-second window.
WINDOW_START = 1_800_000_000 - 1_800_000_000 % 30


class FakeClock:
    def __init__(self, now: float):
        self.now = now
        self.slept: list[float] = []

    def time(self) -> float:
        return self.now

    def sleep(self, seconds: float):
        self.slept.append(seconds)
        self.now += seconds


@pytest.fixture()
def clock(monkeypatch):
    def at(now: float) -> FakeClock:
        fake = FakeClock(now)
        # Only the helper's clock: patching the time module itself would stop every clock in the test run.
        monkeypatch.setattr(totp, "time", fake)
        return fake

    return at


class TestCurrentTotpCode:
    def test_mid_window_it_returns_the_current_code_at_once(self, clock):
        fake = clock(WINDOW_START + 10)

        code = current_totp_code(SECRET)

        assert code == pyotp.TOTP(SECRET).at(WINDOW_START + 10)
        assert fake.slept == []

    def test_near_a_windows_end_it_waits_for_the_next_one(self, clock):
        fake = clock(WINDOW_START + 27)

        code = current_totp_code(SECRET)

        assert fake.now > WINDOW_START + 30
        assert code == pyotp.TOTP(SECRET).at(WINDOW_START + 30)
        assert code != pyotp.TOTP(SECRET).at(WINDOW_START + 27)

    def test_it_waits_as_little_as_it_can(self, clock):
        fake = clock(WINDOW_START + 27)

        current_totp_code(SECRET)

        assert fake.slept == [pytest.approx(3.1)]
