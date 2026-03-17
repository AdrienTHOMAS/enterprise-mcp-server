"""Smart rate limiting — token bucket per service with transparent retry."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

# ── Default rate limits per service ──────────────────────────────────

DEFAULT_LIMITS: dict[str, dict[str, float]] = {
    "jira":      {"rate": 100 / 60, "burst": 20},      # 100 req/min
    "github":    {"rate": 60 / 60, "burst": 10},        # 60 req/min (REST)
    "confluence": {"rate": 100 / 60, "burst": 20},      # 100 req/min
    "slack":     {"rate": 1.0, "burst": 3},              # 1 req/sec per channel
    "pagerduty": {"rate": 200 / 60, "burst": 30},       # 200 req/min
    "datadog":   {"rate": 300 / 60, "burst": 50},       # 300 req/min
}

MAX_WAIT_SECONDS = 30.0


class TokenBucket:
    """Async token bucket rate limiter (in-memory)."""

    def __init__(self, rate: float, burst: int) -> None:
        self._rate = rate          # tokens per second
        self._burst = float(burst)
        self._tokens = float(burst)
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self._burst, self._tokens + elapsed * self._rate)
        self._last_refill = now

    async def acquire(self, timeout: float = MAX_WAIT_SECONDS) -> bool:
        """Wait for a token. Returns True if acquired, False if timed out."""
        deadline = time.monotonic() + timeout
        while True:
            async with self._lock:
                self._refill()
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return True
                wait_time = (1.0 - self._tokens) / self._rate
            if time.monotonic() + wait_time > deadline:
                return False
            await asyncio.sleep(min(wait_time, 0.5))

    @property
    def remaining(self) -> int:
        self._refill()
        return int(self._tokens)

    @property
    def reset_in(self) -> float:
        if self._tokens >= self._burst:
            return 0.0
        return round((self._burst - self._tokens) / self._rate, 1)

    def status(self) -> dict[str, Any]:
        self._refill()
        return {
            "remaining": int(self._tokens),
            "burst": int(self._burst),
            "rate_per_sec": round(self._rate, 2),
            "reset_in_seconds": self.reset_in,
        }


class RateLimiterManager:
    """Manage per-service rate limiters with transparent waiting."""

    def __init__(
        self,
        limits: dict[str, dict[str, float]] | None = None,
    ) -> None:
        self._limits = limits or DEFAULT_LIMITS
        self._buckets: dict[str, TokenBucket] = {}

    def _get_bucket(self, service: str) -> TokenBucket:
        if service not in self._buckets:
            config = self._limits.get(service, {"rate": 10.0, "burst": 10})
            self._buckets[service] = TokenBucket(
                rate=config["rate"],
                burst=int(config["burst"]),
            )
        return self._buckets[service]

    async def acquire(self, service: str) -> bool:
        """Acquire a rate limit token for the given service. Waits transparently."""
        bucket = self._get_bucket(service)
        acquired = await bucket.acquire()
        if not acquired:
            logger.warning(
                "rate_limit_timeout",
                extra={"service": service, "timeout": MAX_WAIT_SECONDS},
            )
        return acquired

    def status(self) -> dict[str, dict[str, Any]]:
        """Return rate limit status for all services (for health endpoint)."""
        result: dict[str, dict[str, Any]] = {}
        for service in self._limits:
            bucket = self._get_bucket(service)
            result[service] = bucket.status()
        return result


# ── Module-level singleton ───────────────────────────────────────────

_rate_limiter: RateLimiterManager | None = None


def get_rate_limiter() -> RateLimiterManager:
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiterManager()
    return _rate_limiter
