"""Tests for Knowledge base caching and JWT Logout blacklist via Redis."""

import pytest
from fastapi.testclient import TestClient

from backend.app.services.cache import get_cache_service


class InMemoryRedis:
    def __init__(self):
        self.store = {}
        self.expirations = {}

    def get(self, name: str):
        val = self.store.get(name)
        if isinstance(val, str):
            return val.encode("utf-8")
        return val

    def set(self, name: str, value: str | bytes, ex: int | None = None, px: int | None = None):
        if isinstance(value, bytes):
            self.store[name] = value
        else:
            self.store[name] = str(value).encode("utf-8")
        return True

    def delete(self, *names: str):
        count = 0
        for name in names:
            if name in self.store:
                del self.store[name]
                count += 1
        return count

    def incr(self, name: str):
        val = int(self.store.get(name, 0)) + 1
        self.store[name] = str(val).encode("utf-8")
        return val

    def expire(self, name: str, time_sec: int):
        return True

    def ping(self):
        return True

    def flushdb(self):
        self.store.clear()


@pytest.fixture(autouse=True)
def clean_cache():
    cache = get_cache_service()
    if not cache.is_connected():
        cache._client = InMemoryRedis()
        cache._connected = True
    else:
        try:
            cache._client.flushdb()
        except Exception:
            pass
    yield
def test_knowledge_base_caching(client: TestClient):
    cache = get_cache_service()

    # 1. First call populates cache
    resp1 = client.get("/api/v1/knowledge")
    assert resp1.status_code == 200
    cached_list = cache.get_json("knowledge:diseases:list")
    assert cached_list is not None
    assert len(cached_list["items"]) == 8

    # 2. Detail call populates item cache
    resp2 = client.get("/api/v1/knowledge/Rust")
    assert resp2.status_code == 200
    cached_item = cache.get_json("knowledge:disease:rust")
    assert cached_item is not None
    assert cached_item["label"] == "Rust"


def test_auth_logout_blacklists_token(client: TestClient):
    # Register and login
    username = "test_logout_user"
    email = "logout_user@example.com"
    password = "password123"

    reg_resp = client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    assert reg_resp.status_code in (201, 409)

    login_resp = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Verify authenticated request works
    me_resp = client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200

    # Logout
    logout_resp = client.post("/api/v1/auth/logout", headers=headers)
    assert logout_resp.status_code == 200
    assert logout_resp.json()["message"] == "Successfully logged out"

    # Subsequent request using the revoked token must be rejected with 401
    revoked_resp = client.get("/api/v1/auth/me", headers=headers)
    assert revoked_resp.status_code == 401
    assert "revoked" in revoked_resp.json()["detail"].lower()
