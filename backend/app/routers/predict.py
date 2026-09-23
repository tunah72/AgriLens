"""
Prediction endpoint for plant disease diagnosis.
"""

import time
from functools import lru_cache
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlmodel import Session

from backend.app.config import settings
from backend.app.db import crud, get_session
from backend.app.db.orm_models import User
from backend.app.knowledge.knowledge_base import KnowledgeBase
from backend.app.models.schemas import PredictionResponse, TopKPrediction
from backend.app.security import get_optional_current_user
from backend.app.services.inference import InferenceService, InvalidImageError
from backend.app.services.storage import StorageService

router = APIRouter(tags=["prediction"])
knowledge_base = KnowledgeBase()
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


@lru_cache
def get_inference_service() -> InferenceService:
    class_names = InferenceService.load_class_names(settings.CLASS_NAMES_PATH)
    return InferenceService(settings.MODEL_PATH, class_names, settings.MODEL_INPUT_SIZE)


@lru_cache
def get_storage_service() -> StorageService:
    return StorageService(
        endpoint=settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        bucket=settings.MINIO_BUCKET,
        secure=settings.MINIO_SECURE,
    )


@lru_cache
def get_knowledge_base() -> KnowledgeBase | None:
    try:
        return KnowledgeBase()
    except NotImplementedError:
        return None


async def read_valid_image(file: UploadFile) -> bytes:
    """Validate and read an uploaded leaf image."""
    if file.content_type and file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Uploaded file must be an image")

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Uploaded file is too large")
    return image_bytes


def build_recommendation(prediction: str, confidence: float) -> dict | None:
    knowledge_base = get_knowledge_base()
    if knowledge_base is None:
        return None
    return knowledge_base.format_recommendation(prediction, confidence)


@router.post("/predict", response_model=PredictionResponse)
async def predict(
    file: UploadFile = File(...),
    crop: Literal["rice", "coffee"] | None = Query(None, description="Optional crop filter: 'rice' or 'coffee'"),
    session: Session = Depends(get_session),
    current_user: User | None = Depends(get_optional_current_user),
):
    """Receive a leaf image, run ONNX inference, save metadata, and return top-k predictions."""
    image_bytes = await read_valid_image(file)

    try:
        inference = get_inference_service()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Inference service unavailable: {exc}",
        ) from exc

    started_at = time.perf_counter()
    try:
        top_k = inference.predict(image_bytes, filename=file.filename, crop=crop, top_k=5)
    except InvalidImageError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image file: {exc}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference failed: {exc}",
        ) from exc
    latency_ms = (time.perf_counter() - started_at) * 1000

    prediction, confidence = top_k[0]
    top_k_payload = [{"label": label, "confidence": score} for label, score in top_k]
    recommendation = build_recommendation(prediction, confidence)

    storage = get_storage_service()
    object_key = None
    try:
        object_key = storage.upload_image(
            image_bytes,
            filename=file.filename or "leaf.jpg",
            content_type=file.content_type or "image/jpeg",
        )
        image_url = storage.get_url(object_key)
        image = crud.create_image_record(
            session=session,
            object_key=object_key,
            user_id=current_user.id if current_user else None,
            original_filename=file.filename,
            content_type=file.content_type,
            size_bytes=len(image_bytes),
            commit=False,
        )
        prediction_record = crud.create_prediction_record(
            session=session,
            image_id=image.id,
            user_id=current_user.id if current_user else None,
            predicted_label=prediction,
            confidence=confidence,
            top_k=top_k_payload,
            recommendation=recommendation,
            model_version=settings.MODEL_VERSION,
            latency_ms=latency_ms,
            commit=False,
        )
        session.commit()
    except Exception as exc:
        session.rollback()
        if object_key:
            try:
                storage.delete_image(object_key)
            except Exception as storage_exc:
                print(f"Warning: Failed to clean up orphaned image '{object_key}': {storage_exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Storage or database unavailable: {exc}",
        ) from exc

    try:
        session.refresh(image)
        session.refresh(prediction_record)
    except Exception as exc:
        print(f"Warning: Failed to refresh db instances post-commit: {exc}")

    return PredictionResponse(
        prediction=prediction,
        confidence=confidence,
        top_k=[TopKPrediction(**item) for item in top_k_payload],
        recommendation=recommendation,
        image_id=str(image.id),
        image_url=image_url,
        prediction_id=str(prediction_record.id),
        latency_ms=latency_ms,
    )
