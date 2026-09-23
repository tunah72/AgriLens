"""Shared fixtures for the end-to-end API tests.

The test stack replaces only infrastructure boundaries (database, ONNX Runtime,
and MinIO). Auth, request validation, routing, persistence, and history
querying use the real FastAPI application code.
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from backend.app.db.database import get_session
from backend.app.main import app
from backend.app.routers import history as history_router
from backend.app.routers import predict as predict_router


class FakeInference:
    """Deterministic ONNX boundary used to keep E2E tests self-contained."""

    def predict(
        self,
        image_bytes: bytes,
        filename: str | None = None,
        crop: str | None = None,
        top_k: int = 5,
    ) -> list[tuple[str, float]]:
        assert image_bytes
        assert top_k == 5
        return [("LeafBlast", 0.91), ("BrownSpot", 0.07)]


class FakeStorage:
    """In-memory MinIO boundary with the same public methods as StorageService."""

    def upload_image(self, image_bytes: bytes, filename: str, content_type: str) -> str:
        assert image_bytes
        assert content_type.startswith("image/")
        return f"predictions/{filename}"

    def get_url(self, object_key: str) -> str:
        return f"https://storage.test/{object_key}"


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """A full API client backed by an isolated in-memory SQLite database."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def override_session() -> Iterator[Session]:
        with Session(engine) as session:
            yield session

    monkeypatch.setattr(predict_router, "get_inference_service", lambda: FakeInference())
    monkeypatch.setattr(predict_router, "get_storage_service", lambda: FakeStorage())
    monkeypatch.setattr(history_router, "get_storage_service", lambda: FakeStorage())
    app.dependency_overrides[get_session] = override_session
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        SQLModel.metadata.drop_all(engine)
