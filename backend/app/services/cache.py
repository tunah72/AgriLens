"""Redis caching and rate limiting service with graceful fallback."""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from typing import Any

import redis

from backend.app.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Production Redis caching client with automatic fallback upon connectivity failure."""

    def __init__(
        self,
        redis_url: str | None = None,
        enabled: bool = True,
        socket_timeout: float = 2.0,
    ) -> None:
        self.enabled = enabled
        self.redis_url = redis_url or settings.REDIS_URL
        self.socket_timeout = socket_timeout
        self._client: redis.Redis | None = None
        self._connected: bool = False

        if self.enabled:
            self._init_client()

    def _init_client(self) -> None:
        """Initialize Redis connection pool."""
        try:
            pool = redis.ConnectionPool.from_url(
                self.redis_url,
                socket_timeout=self.socket_timeout,
                socket_connect_timeout=self.socket_timeout,
                max_connections=20,
                decode_responses=False,
            )
            self._client = redis.Redis(connection_pool=pool)
            self._connected = True
        except Exception as exc:
            logger.warning("Failed to initialize Redis connection pool (%s): %s", self.redis_url, exc)
            self._client = None
            self._connected = False

    def is_connected(self) -> bool:
        """Check if Redis connection is active and responsive."""
        if not self.enabled or self._client is None:
            return False
        try:
            return bool(self._client.ping())
        except Exception:
            return False

    def health_check(self) -> bool:
        """Return True if Redis is healthy and reachable."""
        return self.is_connected()

    def get(self, key: str) -> str | None:
        """Retrieve a string value from Redis."""
        if not self.enabled or self._client is None:
            return None
        try:
            val = self._client.get(key)
            if val is None:
                return None
            return val.decode("utf-8") if isinstance(val, bytes) else str(val)
        except Exception as exc:
            logger.warning("Redis GET error for key '%s': %s", key, exc)
            return None

    def set(self, key: str, value: str, expire: int | None = None) -> bool:
        """Store a string value in Redis with optional TTL in seconds."""
        if not self.enabled or self._client is None:
            return False
        try:
            return bool(self._client.set(key, value, ex=expire))
        except Exception as exc:
            logger.warning("Redis SET error for key '%s': %s", key, exc)
            return False

    def delete(self, key: str) -> bool:
        """Delete a key from Redis."""
        if not self.enabled or self._client is None:
            return False
        try:
            return bool(self._client.delete(key))
        except Exception as exc:
            logger.warning("Redis DELETE error for key '%s': %s", key, exc)
            return False

    def get_json(self, key: str) -> Any | None:
        """Retrieve and deserialize JSON data from Redis."""
        raw = self.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except Exception as exc:
            logger.warning("JSON decode error for Redis key '%s': %s", key, exc)
            return None

    def set_json(self, key: str, value: Any, expire: int | None = None) -> bool:
        """Serialize and store data as JSON with optional TTL."""
        try:
            payload = json.dumps(value, ensure_ascii=False)
            return self.set(key, payload, expire=expire)
        except Exception as exc:
            logger.warning("JSON encode error for Redis key '%s': %s", key, exc)
            return False

    def incr(self, key: str, expire: int | None = None) -> int | None:
        """Atomically increment integer value; sets TTL on first creation."""
        if not self.enabled or self._client is None:
            return None
        try:
            val = self._client.incr(key)
            if expire and val == 1:
                self._client.expire(key, expire)
            return int(val)
        except Exception as exc:
            logger.warning("Redis INCR error for key '%s': %s", key, exc)
            return None

    def close(self) -> None:
        """Close connection pool."""
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass


@lru_cache
def get_cache_service() -> CacheService:
    """Return singleton CacheService instance."""
    return CacheService(
        redis_url=settings.REDIS_URL,
        enabled=settings.REDIS_ENABLED,
        socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
    )
