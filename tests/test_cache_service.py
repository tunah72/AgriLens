"""Unit tests for CacheService and Redis integration."""

import time
from unittest.mock import MagicMock

import pytest
import redis

from backend.app.services.cache import CacheService


class DummyRedis:
    """In-memory mock of Redis client for deterministic unit testing."""

    def __init__(self):
        self.store = {}
        self.expirations = {}

    def get(self, name: str):
        if name in self.expirations and time.time() > self.expirations[name]:
            del self.store[name]
            del self.expirations[name]
            return None
        val = self.store.get(name)
        if isinstance(val, str):
            return val.encode("utf-8")
        return val

    def set(self, name: str, value: str | bytes, ex: int | None = None, px: int | None = None):
        if isinstance(value, bytes):
            self.store[name] = value
        else:
            self.store[name] = str(value).encode("utf-8")
        if ex:
            self.expirations[name] = time.time() + ex
        return True

    def delete(self, *names: str):
        count = 0
        for name in names:
            if name in self.store:
                del self.store[name]
                count += 1
            if name in self.expirations:
                del self.expirations[name]
        return count

    def incr(self, name: str):
        val = int(self.store.get(name, 0)) + 1
        self.store[name] = str(val).encode("utf-8")
        return val

    def expire(self, name: str, time_sec: int):
        if name in self.store:
            self.expirations[name] = time.time() + time_sec
            return True
        return False

    def ping(self):
        return True


@pytest.fixture
def mock_cache_service():
    service = CacheService(redis_url="redis://localhost:6379/0", enabled=True)
    service._client = DummyRedis()
    service._connected = True
    return service


def test_cache_set_and_get(mock_cache_service):
    assert mock_cache_service.set("test_key", "test_value") is True
    assert mock_cache_service.get("test_key") == "test_value"
    assert mock_cache_service.get("non_existent_key") is None


def test_cache_set_and_get_json(mock_cache_service):
    data = {"disease": "Rust", "confidence": 0.95, "symptoms": ["yellow spots"]}
    assert mock_cache_service.set_json("disease:rust", data, expire=60) is True
    retrieved = mock_cache_service.get_json("disease:rust")
    assert retrieved == data


def test_cache_delete(mock_cache_service):
    mock_cache_service.set("to_delete", "value")
    assert mock_cache_service.get("to_delete") == "value"
    assert mock_cache_service.delete("to_delete") is True
    assert mock_cache_service.get("to_delete") is None


def test_cache_incr_with_expire(mock_cache_service):
    count1 = mock_cache_service.incr("rate_limit:client_1", expire=60)
    assert count1 == 1
    count2 = mock_cache_service.incr("rate_limit:client_1", expire=60)
    assert count2 == 2


def test_cache_health_check(mock_cache_service):
    assert mock_cache_service.health_check() is True


def test_cache_graceful_fallback_when_redis_error():
    service = CacheService(redis_url="redis://invalid-host:6379/0", enabled=True)
    # Simulate broken client throwing ConnectionError
    failing_client = MagicMock()
    failing_client.get.side_effect = redis.ConnectionError("Redis down")
    failing_client.set.side_effect = redis.ConnectionError("Redis down")
    failing_client.delete.side_effect = redis.ConnectionError("Redis down")
    failing_client.incr.side_effect = redis.ConnectionError("Redis down")
    failing_client.ping.side_effect = redis.ConnectionError("Redis down")

    service._client = failing_client
    service._connected = True

    # Should not raise exceptions; returns safe fallbacks
    assert service.get("any_key") is None
    assert service.set("any_key", "val") is False
    assert service.delete("any_key") is False
    assert service.get_json("any_key") is None
    assert service.set_json("any_key", {"a": 1}) is False
    assert service.incr("rate:key") is None
    assert service.health_check() is False


def test_cache_disabled():
    service = CacheService(enabled=False)
    assert service.set("key", "val") is False
    assert service.get("key") is None
    assert service.delete("key") is False
    assert service.health_check() is False
