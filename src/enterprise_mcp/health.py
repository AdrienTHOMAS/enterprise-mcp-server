"""Health check HTTP server and circuit breaker implementation."""

import asyncio
import time
from collections import deque
from enum import Enum
from typing import Any

import structlog
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from . import __version__
from .cache import get_cache
from .observability import get_tool_metrics

logger = structlog.get_logger("health")

# ---- Circuit Breaker ----------------------------------------------------- #


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker pattern for external service calls.

    CLOSED -> OPEN after `failure_threshold` errors within `window_seconds`.
    OPEN -> HALF_OPEN after `recovery_timeout` seconds.
    HALF_OPEN -> CLOSED on success, OPEN on failure.
    """

    def __init__(
        self,
        service_name: str,
        failure_threshold: int = 5,
        window_seconds: float = 60.0,
        recovery_timeout: float = 30.0,
    ) -> None:
        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self.window_seconds = window_seconds
        self.recovery_timeout = recovery_timeout

        self._state = CircuitState.CLOSED
        self._failures: deque[float] = deque()
        self._opened_at: float = 0.0
        self._half_open_in_progress = False

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if time.monotonic() - self._opened_at >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._half_open_in_progress = False
                logger.info(
                    "circuit_state_change",
                    service=self.service_name,
                    from_state="open",
                    to_state="half_open",
                )
        return self._state

    def record_success(self) -> None:
        """Record a successful call."""
        if self._state in (CircuitState.HALF_OPEN, CircuitState.OPEN):
            old_state = self._state
            self._state = CircuitState.CLOSED
            self._failures.clear()
            self._half_open_in_progress = False
            logger.info(
                "circuit_state_change",
                service=self.service_name,
                from_state=old_state.value,
                to_state="closed",
            )

    def record_failure(self) -> None:
        """Record a failed call."""
        now = time.monotonic()

        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.OPEN
            self._opened_at = now
            logger.warning(
                "circuit_state_change",
                service=self.service_name,
                from_state="half_open",
                to_state="open",
            )
            return

        self._failures.append(now)

        # Purge failures outside the window
        cutoff = now - self.window_seconds
        while self._failures and self._failures[0] < cutoff:
            self._failures.popleft()

        if len(self._failures) >= self.failure_threshold:
            old_state = self._state
            self._state = CircuitState.OPEN
            self._opened_at = now
            logger.warning(
                "circuit_state_change",
                service=self.service_name,
                from_state=old_state.value,
                to_state="open",
                failure_count=len(self._failures),
            )

    def allow_request(self) -> bool:
        """Check if a request should be allowed through."""
        current = self.state
        if current == CircuitState.CLOSED:
            return True
        if current == CircuitState.HALF_OPEN:
            if not self._half_open_in_progress:
                self._half_open_in_progress = True
                return True
            return False
        return False

    def status(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "recent_failures": len(self._failures),
            "failure_threshold": self.failure_threshold,
        }


# Global circuit breaker registry
_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(service_name: str) -> CircuitBreaker:
    """Get or create a circuit breaker for a service."""
    if service_name not in _breakers:
        _breakers[service_name] = CircuitBreaker(service_name)
    return _breakers[service_name]


# ---- Health Check Server ------------------------------------------------- #

_start_time = time.monotonic()

# Service connectivity check callables
_health_checks: dict[str, Any] = {}


def register_health_check(service_name: str, check_fn: Any) -> None:
    """Register a connectivity check function for a service."""
    _health_checks[service_name] = check_fn


async def check_service_health(service_name: str) -> dict[str, Any]:
    """Run health check for a single service."""
    check_fn = _health_checks.get(service_name)
    if check_fn is None:
        return {"status": "unknown", "message": "No health check registered"}
    try:
        start = time.monotonic()
        await asyncio.wait_for(check_fn(), timeout=5.0)
        latency_ms = (time.monotonic() - start) * 1000
        breaker = _breakers.get(service_name)
        return {
            "status": "healthy",
            "latency_ms": round(latency_ms, 2),
            "circuit_breaker": breaker.status() if breaker else None,
        }
    except asyncio.TimeoutError:
        return {"status": "unhealthy", "message": "Health check timed out"}
    except Exception as exc:
        return {"status": "unhealthy", "message": str(exc)}


async def get_overall_health() -> dict[str, Any]:
    """Compute overall system health status."""
    services: dict[str, Any] = {}
    statuses: list[str] = []

    for name in _health_checks:
        result = await check_service_health(name)
        services[name] = result
        statuses.append(result["status"])

    # Add cache health
    cache = get_cache()
    cache_stats = cache.stats()
    services["cache"] = {
        "status": "healthy",
        "stats": cache_stats,
    }

    if all(s == "healthy" for s in statuses):
        overall = "healthy"
    elif any(s == "unhealthy" for s in statuses):
        overall = "degraded"
    else:
        overall = "healthy"

    uptime = time.monotonic() - _start_time

    return {
        "status": overall,
        "version": __version__,
        "uptime_seconds": round(uptime, 1),
        "services": services,
        "tool_metrics": get_tool_metrics(),
    }


def create_health_app() -> FastAPI:
    """Create the FastAPI health check application."""
    health_app = FastAPI(title="Enterprise MCP Health", version=__version__)

    @health_app.get("/health")
    async def health_endpoint() -> JSONResponse:
        health_data = await get_overall_health()
        status_code = 200 if health_data["status"] != "unhealthy" else 503
        return JSONResponse(content=health_data, status_code=status_code)

    @health_app.get("/health/ready")
    async def readiness() -> JSONResponse:
        health_data = await get_overall_health()
        if health_data["status"] == "unhealthy":
            return JSONResponse(content={"ready": False}, status_code=503)
        return JSONResponse(content={"ready": True}, status_code=200)

    @health_app.get("/health/live")
    async def liveness() -> JSONResponse:
        return JSONResponse(content={"alive": True}, status_code=200)

    return health_app
