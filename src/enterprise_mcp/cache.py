"""Redis-backed caching with in-memory fallback."""

import hashlib
import json
import time
from typing import Any

import structlog

logger = structlog.get_logger("cache")

# Default TTLs per resource type (seconds)
DEFAULT_TTLS: dict[str, int] = {
    "jira": 60,
    "github": 300,
    "confluence": 120,
    "slack": 600,
    "pagerduty": 30,
    "datadog": 30,
    "default": 120,
}


class InMemoryBackend:
    """Simple in-memory cache backend with TTL support."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, float]] = {}
        self._hits = 0
        self._misses = 0

    async def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            self._misses += 1
            return None
        value, expires_at = entry
        if time.monotonic() > expires_at:
            del self._store[key]
            self._misses += 1
            return None
        self._hits += 1
        return value

    async def set(self, key: str, value: Any, ttl: int = 120) -> None:
        self._store[key] = (value, time.monotonic() + ttl)

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def delete_pattern(self, pattern: str) -> int:
        prefix = pattern.rstrip("*")
        keys_to_delete = [k for k in self._store if k.startswith(prefix)]
        for k in keys_to_delete:
            del self._store[k]
        return len(keys_to_delete)

    async def flush(self) -> None:
        self._store.clear()

    def stats(self) -> dict[str, Any]:
        total = self._hits + self._misses
        return {
            "backend": "memory",
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total, 4) if total > 0 else 0.0,
            "keys": len(self._store),
        }

    async def ping(self) -> bool:
        return True


class RedisBackend:
    """Redis cache backend using redis.asyncio."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0") -> None:
        self._redis_url = redis_url
        self._client: Any = None
        self._hits = 0
        self._misses = 0

    async def _get_client(self) -> Any:
        if self._client is None:
            import redis.asyncio as aioredis

            self._client = aioredis.from_url(
                self._redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._client

    async def get(self, key: str) -> Any | None:
        client = await self._get_client()
        raw = await client.get(key)
        if raw is None:
            self._misses += 1
            return None
        self._hits += 1
        return json.loads(raw)

    async def set(self, key: str, value: Any, ttl: int = 120) -> None:
        client = await self._get_client()
        await client.setex(key, ttl, json.dumps(value, default=str))

    async def delete(self, key: str) -> None:
        client = await self._get_client()
        await client.delete(key)

    async def delete_pattern(self, pattern: str) -> int:
        client = await self._get_client()
        cursor = 0
        deleted = 0
        while True:
            cursor, keys = await client.scan(cursor, match=pattern, count=100)
            if keys:
                await client.delete(*keys)
                deleted += len(keys)
            if cursor == 0:
                break
        return deleted

    async def flush(self) -> None:
        client = await self._get_client()
        await client.flushdb()

    def stats(self) -> dict[str, Any]:
        total = self._hits + self._misses
        return {
            "backend": "redis",
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total, 4) if total > 0 else 0.0,
            "url": self._redis_url,
        }

    async def ping(self) -> bool:
        try:
            client = await self._get_client()
            return await client.ping()
        except Exception:
            return False

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None


class CacheManager:
    """Unified cache manager with Redis primary and in-memory fallback."""

    def __init__(self, redis_url: str = "", custom_ttls: dict[str, int] | None = None) -> None:
        self._redis: RedisBackend | None = None
        self._memory = InMemoryBackend()
        self._ttls = {**DEFAULT_TTLS, **(custom_ttls or {})}
        self._using_redis = False

        if redis_url:
            self._redis = RedisBackend(redis_url)

    async def initialize(self) -> None:
        """Try to connect to Redis; fall back to memory if unavailable."""
        if self._redis is not None:
            try:
                if await self._redis.ping():
                    self._using_redis = True
                    logger.info("cache_initialized", backend="redis")
                    return
            except Exception as exc:
                logger.warning("redis_unavailable", error=str(exc), fallback="memory")

        self._using_redis = False
        logger.info("cache_initialized", backend="memory")

    @property
    def _backend(self) -> InMemoryBackend | RedisBackend:
        if self._using_redis and self._redis is not None:
            return self._redis
        return self._memory

    def _get_ttl(self, resource_type: str) -> int:
        return self._ttls.get(resource_type, self._ttls["default"])

    @staticmethod
    def _make_key(resource_type: str, operation: str, **params: Any) -> str:
        """Generate a deterministic cache key."""
        param_str = json.dumps(params, sort_keys=True, default=str)
        param_hash = hashlib.md5(param_str.encode()).hexdigest()[:12]
        return f"emcp:{resource_type}:{operation}:{param_hash}"

    async def get(self, resource_type: str, operation: str, **params: Any) -> Any | None:
        """Get a cached value."""
        key = self._make_key(resource_type, operation, **params)
        result = await self._backend.get(key)
        if result is not None:
            logger.debug("cache_hit", resource_type=resource_type, operation=operation)
        return result

    async def set(
        self, value: Any, resource_type: str, operation: str, **params: Any
    ) -> None:
        """Set a cached value with resource-type-appropriate TTL."""
        key = self._make_key(resource_type, operation, **params)
        ttl = self._get_ttl(resource_type)
        await self._backend.set(key, value, ttl)
        logger.debug("cache_set", resource_type=resource_type, operation=operation, ttl=ttl)

    async def invalidate(self, resource_type: str, operation: str = "*") -> int:
        """Invalidate cache entries for a resource type."""
        if operation == "*":
            pattern = f"emcp:{resource_type}:*"
        else:
            pattern = f"emcp:{resource_type}:{operation}:*"
        deleted = await self._backend.delete_pattern(pattern)
        logger.info("cache_invalidated", resource_type=resource_type, pattern=pattern, deleted=deleted)
        return deleted

    def stats(self) -> dict[str, Any]:
        """Return cache statistics for health checks."""
        return self._backend.stats()

    async def close(self) -> None:
        """Close backend connections."""
        if self._redis is not None:
            await self._redis.close()


# Module-level singleton
_cache: CacheManager | None = None


def get_cache() -> CacheManager:
    """Get the global cache manager singleton."""
    global _cache
    if _cache is None:
        _cache = CacheManager()
    return _cache


async def init_cache(redis_url: str = "", custom_ttls: dict[str, int] | None = None) -> CacheManager:
    """Initialize and return the global cache manager."""
    global _cache
    _cache = CacheManager(redis_url, custom_ttls)
    await _cache.initialize()
    return _cache
