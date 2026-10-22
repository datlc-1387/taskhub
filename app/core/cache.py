import json
import logging
import time
from typing import Any, Protocol

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import get_settings

logger = logging.getLogger("taskhub.cache")


class CacheBackend(Protocol):
    async def get(self, key: str) -> Any | None: ...
    async def set(self, key: str, value: Any, ttl: int) -> None: ...
    async def delete_prefix(self, prefix: str) -> None: ...


class InMemoryCache:
    def __init__(self) -> None:
        self._store: dict[str, tuple[float, str]] = {}

    async def get(self, key: str) -> Any | None:
        item = self._store.get(key)
        if item is None:
            return None
        expires_at, raw = item
        if expires_at < time.monotonic():
            del self._store[key]
            return None
        return json.loads(raw)

    async def set(self, key: str, value: Any, ttl: int) -> None:
        self._store[key] = (time.monotonic() + ttl, json.dumps(value, default=str))

    async def delete_prefix(self, prefix: str) -> None:
        for key in [k for k in self._store if k.startswith(prefix)]:
            del self._store[key]


class RedisCache:
    def __init__(self, url: str, timeout: float) -> None:
        self._redis: Redis = Redis.from_url(
            url, decode_responses=True, socket_timeout=timeout, socket_connect_timeout=timeout
        )

    async def get(self, key: str) -> Any | None:
        try:
            raw = await self._redis.get(key)
        except RedisError:
            logger.warning("Redis unavailable, cache miss for %s", key)
            return None
        return None if raw is None else json.loads(raw)

    async def set(self, key: str, value: Any, ttl: int) -> None:
        try:
            await self._redis.set(key, json.dumps(value, default=str), ex=ttl)
        except RedisError:
            logger.warning("Redis unavailable, skip caching %s", key)

    async def delete_prefix(self, prefix: str) -> None:
        try:
            keys = [key async for key in self._redis.scan_iter(match=f"{prefix}*", count=500)]
            if keys:
                await self._redis.unlink(*keys)
        except RedisError:
            logger.warning("Redis unavailable, could not invalidate %s", prefix)


_cache: CacheBackend | None = None


def get_cache() -> CacheBackend:
    global _cache
    if _cache is None:
        settings = get_settings()
        url = settings.redis_url
        _cache = RedisCache(url, settings.redis_timeout_seconds) if url else InMemoryCache()
    return _cache
