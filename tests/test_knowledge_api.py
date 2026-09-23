import os

os.environ["SKIP_DB_INIT"] = "true"

import asyncio
from io import BytesIO
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from backend.app.main import app
from backend.app.routers import predict as predict_router
from backend.app.routers.knowledge import get_knowledge, list_knowledge
from backend.app.routers.predict import build_recommendation, predict, read_valid_image


class FakeUploadFile:
    def __init__(self, content: bytes, content_type: str = "image/jpeg"):
        self.filename = "leaf.jpg"
        self.content_type = content_type
        self.file = BytesIO(content)

    async def read(self) -> bytes:
        return self.file.read()


def test_list_knowledge_returns_supported_diseases():
    response = asyncio.run(list_knowledge())

    assert response.total == 8
    assert len(response.items) == 8
    assert response.items[0].label
    assert response.items[0].crop
    assert response.items[0].name_vi
    assert response.items[0].name_en
    assert response.items[0].severity


def test_get_knowledge_returns_disease_detail():
    response = asyncio.run(get_knowledge("BrownSpot"))

    assert response.label == "BrownSpot"
    assert response.crop == "rice"
    assert response.treatments
    assert response.prevention
    assert response.sources


def test_get_knowledge_returns_404_for_unknown_label():
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(get_knowledge("InvalidLabel"))
    assert exc_info.value.status_code == 404


def test_openapi_contains_knowledge_and_prediction_contracts():
    payload = app.openapi()
    assert "/api/v1/knowledge" in payload["paths"]
    assert "/api/v1/knowledge/{disease_label}" in payload["paths"]
    assert "/api/v1/predict" in payload["paths"]
    assert "DiseaseRecommendation" in payload["components"]["schemas"]


def test_predict_recommendation_builder_matches_knowledge_contract():
    recommendation = build_recommendation("LeafBlast", 0.72)

    assert recommendation["label"] == "LeafBlast"
    assert recommendation["confidence"] == 0.72
    assert recommendation["treatments"]
    assert recommendation["prevention"]


def _upload_file(content: bytes, content_type: str = "image/jpeg") -> FakeUploadFile:
    return FakeUploadFile(content, content_type)


def test_predict_upload_validation_accepts_supported_image():
    image_bytes = asyncio.run(read_valid_image(_upload_file(b"image-bytes", "image/png")))

    assert image_bytes == b"image-bytes"


def test_predict_upload_validation_rejects_empty_file():
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(read_valid_image(_upload_file(b"")))
    assert exc_info.value.status_code == 400


def test_predict_upload_validation_rejects_unsupported_type():
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(read_valid_image(_upload_file(b"not-image", "text/plain")))
    assert exc_info.value.status_code == 415


def test_predict_returns_service_unavailable_when_inference_is_unavailable(monkeypatch):
    def unavailable_inference():
        raise FileNotFoundError("missing model")

    monkeypatch.setattr(predict_router, "get_inference_service", unavailable_inference)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(predict(_upload_file(b"image-bytes")))
    assert exc_info.value.status_code == 503
    assert "Inference service unavailable" in exc_info.value.detail


def test_predict_upload_runs_inference_storage_and_db(monkeypatch):
    image_id = uuid4()
    prediction_id = uuid4()
    uploaded = {}

    class FakeInference:
        def predict(
            self,
            image_bytes: bytes,
            filename: str | None = None,
            crop: str | None = None,
            top_k: int = 5,
        ):
            assert image_bytes == b"image-bytes"
            assert top_k == 5
            return [("LeafBlast", 0.82), ("BrownSpot", 0.12)]

    class FakeStorage:
        def upload_image(self, image_bytes: bytes, filename: str, content_type: str):
            uploaded.update(
                {
                    "image_bytes": image_bytes,
                    "filename": filename,
                    "content_type": content_type,
                }
            )
            return "predictions/leaf.jpg"

        def get_url(self, object_key: str):
            return f"https://storage.local/{object_key}"

        def delete_image(self, object_key: str):
            pass

    class FakeSession:
        rolled_back = False
        committed = False

        def commit(self):
            self.committed = True

        def refresh(self, instance):
            pass

        def rollback(self):
            self.rolled_back = True

    def create_image_record(**kwargs):
        assert kwargs["object_key"] == "predictions/leaf.jpg"
        assert kwargs["original_filename"] == "leaf.jpg"
        assert kwargs["content_type"] == "image/jpeg"
        assert kwargs["size_bytes"] == len(b"image-bytes")
        return SimpleNamespace(id=image_id)

    def create_prediction_record(**kwargs):
        assert kwargs["image_id"] == image_id
        assert kwargs["predicted_label"] == "LeafBlast"
        assert kwargs["confidence"] == 0.82
        assert kwargs["top_k"] == [
            {"label": "LeafBlast", "confidence": 0.82},
            {"label": "BrownSpot", "confidence": 0.12},
        ]
        assert kwargs["recommendation"]["label"] == "LeafBlast"
        return SimpleNamespace(id=prediction_id)

    monkeypatch.setattr(predict_router, "get_inference_service", lambda: FakeInference())
    monkeypatch.setattr(predict_router, "get_storage_service", lambda: FakeStorage())
    monkeypatch.setattr(predict_router.crud, "create_image_record", create_image_record)
    monkeypatch.setattr(predict_router.crud, "create_prediction_record", create_prediction_record)

    session = FakeSession()
    response = asyncio.run(predict(_upload_file(b"image-bytes"), session=session, current_user=None))

    assert uploaded == {
        "image_bytes": b"image-bytes",
        "filename": "leaf.jpg",
        "content_type": "image/jpeg",
    }
    assert response.prediction == "LeafBlast"
    assert response.confidence == 0.82
    assert response.top_k[0].label == "LeafBlast"
    assert response.recommendation.label == "LeafBlast"
    assert response.image_id == str(image_id)
    assert response.prediction_id == str(prediction_id)
    assert response.image_url == "https://storage.local/predictions/leaf.jpg"
    assert response.latency_ms is not None
    assert not session.rolled_back


def test_predict_rejects_corrupted_image(monkeypatch):
    from backend.app.services.inference import InvalidImageError

    class FakeInference:
        def predict(self, *args, **kwargs):
            raise InvalidImageError("Mocked invalid image content")

    monkeypatch.setattr(predict_router, "get_inference_service", lambda: FakeInference())

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(predict(_upload_file(b"invalid-image-bytes")))
    assert exc_info.value.status_code == 400
    assert "Invalid image file" in exc_info.value.detail
