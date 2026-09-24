"""Tests for Redis-backed Rate Limiter dependency."""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, Request

from backend.app.services.cache import CacheService
from backend.app.services.limiter import RateLimiter


class MockRedis:
    def __init__(self):
        self.counts = {}

    def incr(self, key: str):
        self.counts[key] = self.counts.get(key, 0) + 1
        return self.counts[key]

    def expire(self, key: str, sec: int):
        pass


@pytest.fixture
def mock_cache():
    cache = CacheService(enabled=True)
    cache._client = MockRedis()
    cache._connected = True
    return cache


def make_request(ip: str = "127.0.0.1") -> Request:
    scope = {
        "type": "http",
        "client": (ip, 12345),
        "headers": [(b"host", b"testserver")],
    }
    return Request(scope)


@pytest.mark.asyncio
async def test_rate_limiter_allows_within_limit(mock_cache):
    limiter = RateLimiter(times=3, seconds=60, key_prefix="test", cache_service=mock_cache)
    req = make_request("1.2.3.4")

    # 3 allowed requests
    for _ in range(3):
        await limiter(req)


@pytest.mark.asyncio
async def test_rate_limiter_blocks_over_limit(mock_cache):
    limiter = RateLimiter(times=2, seconds=60, key_prefix="test_block", cache_service=mock_cache)
    req = make_request("1.2.3.4")

    await limiter(req)
    await limiter(req)

    # 3rd request must trigger 429
    with pytest.raises(HTTPException) as exc_info:
        await limiter(req)

    assert exc_info.value.status_code == 429
    assert "Retry-After" in exc_info.value.headers
    assert exc_info.value.headers["Retry-After"] == "60"


@pytest.mark.asyncio
async def test_rate_limiter_fails_open_when_redis_down():
    # Failing cache service returns None on incr
    failing_cache = MagicMock()
    failing_cache.incr.return_value = None

    limiter = RateLimiter(times=1, seconds=60, key_prefix="test_failopen", cache_service=failing_cache)
    req = make_request("1.2.3.4")

    # Should not raise 429 when Redis fails open
    for _ in range(5):
        await limiter(req)


@pytest.mark.asyncio
async def test_rate_limiter_distinct_clients(mock_cache):
    limiter = RateLimiter(times=1, seconds=60, key_prefix="test_clients", cache_service=mock_cache)
    req1 = make_request("10.0.0.1")
    req2 = make_request("10.0.0.2")

    await limiter(req1)
    await limiter(req2)  # Should succeed because client IP is different

    with pytest.raises(HTTPException):
        await limiter(req1)  # req1 exceeded its quota
