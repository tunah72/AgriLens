from fastapi.testclient import TestClient


def test_root_redirects_to_docs(client: TestClient) -> None:
    # Test that accessing the root "/" redirects to "/docs"
    # We pass follow_redirects=False to verify the 307 Temporary Redirect status and headers
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/docs"


def test_api_v1_welcome(client: TestClient) -> None:
    response = client.get("/api/v1")
    assert response.status_code == 200
    data = response.json()
    assert "Welcome" in data["message"]
    assert data["docs"] == "/docs"
    assert data["health"] == "/health"
    assert data["version"] == "0.1.0"
