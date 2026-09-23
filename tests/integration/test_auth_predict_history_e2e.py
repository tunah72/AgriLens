"""Login -> upload image -> prediction -> history E2E coverage."""

from fastapi.testclient import TestClient

# A valid PNG header is sufficient because image decoding is an ONNX concern,
# which is replaced by the deterministic inference boundary in this API test.
SAMPLE_LEAF_PNG = b"\x89PNG\r\n\x1a\ne2e-leaf"


def test_authenticated_user_can_predict_and_review_history(client: TestClient) -> None:
    username = "e2e_user"
    password = "e2e-safe-password"

    registration = client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": "e2e_user@example.test", "password": password},
    )
    assert registration.status_code == 201, registration.text
    assert registration.json()["username"] == username

    login = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    prediction = client.post(
        "/api/v1/predict",
        headers=headers,
        files={"file": ("leaf.png", SAMPLE_LEAF_PNG, "image/png")},
    )
    assert prediction.status_code == 200, prediction.text
    payload = prediction.json()
    assert payload["prediction"] == "LeafBlast"
    assert payload["confidence"] == 0.91
    assert payload["top_k"][0] == {"label": "LeafBlast", "confidence": 0.91}
    assert payload["recommendation"]["label"] == "LeafBlast"
    assert payload["image_url"] == "https://storage.test/predictions/leaf.png"
    assert payload["image_id"]
    assert payload["prediction_id"]
    assert payload["latency_ms"] >= 0

    history = client.get("/api/v1/history", headers=headers)
    assert history.status_code == 200, history.text
    history_payload = history.json()
    assert history_payload["total"] == 1
    assert history_payload["items"][0]["id"] == payload["prediction_id"]
    assert history_payload["items"][0]["image_id"] == payload["image_id"]
    assert history_payload["items"][0]["predicted_label"] == "LeafBlast"


def test_history_requires_a_logged_in_user(client: TestClient) -> None:
    response = client.get("/api/v1/history")
    assert response.status_code == 401


def test_predict_rejects_invalid_crop_type(client: TestClient) -> None:
    response = client.post(
        "/api/v1/predict",
        files={"file": ("leaf.png", SAMPLE_LEAF_PNG, "image/png")},
        params={"crop": "banana"},
    )
    assert response.status_code == 422
