from fastapi import Request

from app.core.errors import RateLimitedError
from app.core.rate_limit import RateLimiter


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def request_from(ip: str) -> Request:
    return Request({"type": "http", "client": (ip, 5000), "headers": []})


def test_blocks_after_the_limit_and_reports_when_to_retry() -> None:
    limiter = RateLimiter(3, 60, clock=FakeClock())
    for _ in range(3):
        limiter(request_from("1.1.1.1"))

    try:
        limiter(request_from("1.1.1.1"))
    except RateLimitedError as error:
        assert 1 <= error.retry_after_seconds <= 60
    else:
        raise AssertionError("4th request should have been blocked")


def test_each_ip_has_its_own_counter() -> None:
    limiter = RateLimiter(1, 60, clock=FakeClock())
    limiter(request_from("1.1.1.1"))

    limiter(request_from("2.2.2.2"))  # a different visitor is unaffected


def test_allowed_again_once_the_window_has_passed() -> None:
    clock = FakeClock()
    limiter = RateLimiter(1, 60, clock=clock)
    limiter(request_from("1.1.1.1"))

    clock.now += 61

    limiter(request_from("1.1.1.1"))


def test_disabled_limiter_never_blocks() -> None:
    limiter = RateLimiter(1, 60, enabled=False, clock=FakeClock())
    for _ in range(10):
        limiter(request_from("1.1.1.1"))
