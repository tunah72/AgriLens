"""Rate limiting dependency backed by Redis."""

from __future__ import annotations

import logging

from fastapi import HTTPException, Request, status

from backend.app.services.cache import CacheService, get_cache_service

logger = logging.getLogger(__name__)


class RateLimiter:
    """FastAPI dependency for rate limiting client requests using Redis."""

    def __init__(
        self,
        times: int,
        seconds: int = 60,
        key_prefix: str = "rate",
        cache_service: CacheService | None = None,
    ) -> None:
        self.times = times
        self.seconds = seconds
        self.key_prefix = key_prefix
        self.cache_service = cache_service

    def _get_cache(self) -> CacheService:
        return self.cache_service if self.cache_service is not None else get_cache_service()

    def _get_client_identifier(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
            if ip:
                return ip
        if request.client and request.client.host:
            return request.client.host
        return "anonymous"

    async def __call__(self, request: Request) -> None:
        cache = self._get_cache()
        if not cache.enabled:
            return

        client_id = self._get_client_identifier(request)
        key = f"ratelimit:{self.key_prefix}:{client_id}"

        count = cache.incr(key, expire=self.seconds)
        if count is None:
            # Redis is unreachable or errored - fail open to avoid service disruption
            return

        if count > self.times:
            logger.warning(
                "Rate limit exceeded for %s on %s (count: %d, limit: %d)",
                client_id,
                self.key_prefix,
                count,
                self.times,
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {self.times} requests per {self.seconds} seconds.",
                headers={"Retry-After": str(self.seconds)},
            )
