import math
import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable

from fastapi import Request

from app.core.config import get_settings
from app.core.errors import RateLimitedError


class RateLimiter:
    """Sliding-window limiter, used as a FastAPI dependency:

        @router.post("/login", dependencies=[Depends(login_limiter)])

    Counts requests per client IP in memory. That is right for a single free-tier
    instance. With several instances each would keep its own counts, and we would
    move the counters to Redis. (We wrote this instead of using slowapi, which is
    barely maintained; this covers our need in ~30 lines.)
    """

    def __init__(
        self,
        max_requests: int,
        window_seconds: int = 60,
        *,
        enabled: bool = True,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.enabled = enabled
        self._clock = clock
        self._hits: defaultdict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()  # sync endpoints run in a thread pool

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()

    def __call__(self, request: Request) -> None:
        if not self.enabled:
            return
        # Behind a proxy this is the proxy's address unless uvicorn is started with
        # --proxy-headers (we do that in production).
        client_ip = request.client.host if request.client else "unknown"
        now = self._clock()
        cutoff = now - self.window_seconds

        with self._lock:
            hits = self._hits[client_ip]
            while hits and hits[0] <= cutoff:
                hits.popleft()
            if len(hits) >= self.max_requests:
                retry_after = max(1, math.ceil(hits[0] + self.window_seconds - now))
                raise RateLimitedError(retry_after)
            hits.append(now)
            if len(self._hits) > 10_000:  # don't let old IPs pile up forever
                self._drop_expired(cutoff)

    def _drop_expired(self, cutoff: float) -> None:
        for ip in [ip for ip, hits in self._hits.items() if not hits or hits[-1] <= cutoff]:
            del self._hits[ip]


def make_auth_limiter() -> RateLimiter:
    settings = get_settings()
    return RateLimiter(
        settings.auth_rate_limit_per_minute,
        enabled=settings.rate_limit_enabled,
    )
