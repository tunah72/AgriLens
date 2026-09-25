"""
Prediction endpoint for plant disease diagnosis.
"""

import time
from functools import lru_cache
from typing import Literal

import gc
from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from sqlmodel import Session

from backend.app.config import settings
from backend.app.db import crud, get_session
from backend.app.db.orm_models import User
from backend.app.knowledge.knowledge_base import KnowledgeBase
from backend.app.models.schemas import DetectionItem, PredictionResponse, TopKPrediction
from backend.app.security import get_optional_current_user
from backend.app.services.inference import InferenceService, InvalidImageError
from backend.app.services.domain_guard import DomainGuard
from backend.app.services.limiter import RateLimiter
from backend.app.services.storage import StorageService

router = APIRouter(tags=["prediction"])
knowledge_base = KnowledgeBase()
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
predict_rate_limiter = RateLimiter(
    times=settings.RATE_LIMIT_PREDICT_PER_MINUTE,
    seconds=60,
    key_prefix="predict",
)
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
    _rate_limit: None = Depends(predict_rate_limiter),
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
    domain_check = DomainGuard.check_image(image_bytes)

    if not domain_check.is_valid_leaf:
        latency_ms = (time.perf_counter() - started_at) * 1000
        prediction = "InvalidLeaf"
        confidence = 0.0
        top_k_payload = []
        detections = []
        annotated_bytes = None
        recommendation = {
            "label": "InvalidLeaf",
            "crop": "none",
            "name_vi": "Không phải phiến lá hợp lệ",
            "name_en": "Invalid Leaf Specimen",
            "description": (
                "Hệ thống phát hiện hình ảnh được tải lên không thuộc phạm vi chẩn đoán nông nghiệp của AgriLens "
                f"({domain_check.reason}). Vui lòng chỉ chụp ảnh phiến lá lúa hoặc lá cà phê."
            ),
            "symptoms": [],
            "causes": [domain_check.reason or "Hình ảnh không khớp với đặc trưng của lá lúa hoặc cà phê."],
            "treatments": [],
            "prevention": [
                "Chụp ảnh cận cảnh phiến lá rõ nét, đủ ánh sáng tự nhiên.",
                "Tránh chụp văn bản, giấy tờ, tài liệu, con dấu, hoa quả hoặc vật thể lạ.",
                "Đảm bảo phiến lá chiếm phần lớn khung hình để AI phân tích chính xác nhất.",
            ],
            "severity": "None",
            "sources": [],
            "confidence": 0.0,
            "confidence_note": "Ảnh ngoài miền chẩn đoán (Out-of-domain).",
            "confidence_note_vi": "Ảnh ngoài miền chẩn đoán (Out-of-domain).",
            "advisory": (
                "This image does not contain a valid rice or coffee leaf specimen. "
                "Please capture a clear leaf photo for accurate diagnosis."
            ),
            "advisory_vi": (
                "Hình ảnh này không chứa phiến lá lúa hoặc cà phê hợp lệ. "
                "Vui lòng chụp ảnh phiến lá rõ nét trên đồng ruộng để hệ thống đưa ra chẩn đoán chính xác."
            ),
            "is_valid_leaf": False,
            "domain_warning": domain_check.reason,
            "domain_warning_en": domain_check.reason_en,
        }
    else:
        try:
            if hasattr(inference, "predict_segmentation"):
                top_k, detections, annotated_bytes = inference.predict_segmentation(
                    image_bytes, filename=file.filename, crop=crop, top_k=3
                )
            else:
                top_k = inference.predict(image_bytes, filename=file.filename, crop=crop, top_k=3)
                detections = []
                annotated_bytes = None
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

        if detections:
            filtered_detections = DomainGuard.filter_spurious_detections(detections)
            if not filtered_detections and top_k and top_k[0][0] != "Healthy":
                # Spurious detections removed -> fallback to Healthy
                top_k = [("Healthy", 0.95)] + [item for item in top_k if item[0] != "Healthy"][:2]
                detections = []
                annotated_bytes = None
            else:
                detections = filtered_detections

        prediction, confidence = top_k[0] if top_k else ("Healthy", 0.95)
        top_k_payload = [{"label": label, "confidence": score} for label, score in top_k]
        recommendation = build_recommendation(prediction, confidence)
        if prediction == "Healthy" and not detections and isinstance(recommendation, dict):
            recommendation["advisory_vi"] = (
                "Khuyến nghị chỉ mang tính chất tham khảo dựa trên ảnh phân tích. "
                "Hệ thống AI được tối ưu chuyên biệt cho lá lúa và lá cà phê; "
                "nếu ảnh tải lên là hoa, cây cảnh khác hoặc dị vật, kết quả chẩn đoán này không phản ánh đúng thực tế."
            )
            recommendation["advisory"] = (
                "Recommendations are for reference based on the input image. AgriLens is specialized for rice and coffee foliage; "
                "if the uploaded image contains flowers, ornamentals, or non-leaf objects, this diagnosis is not applicable."
            )
    storage = get_storage_service()
    object_key = None
    annotated_object_key = None
    annotated_image_url = None
    try:
        object_key = storage.upload_image(
            image_bytes,
            filename=file.filename or "leaf.jpg",
            content_type=file.content_type or "image/jpeg",
        )
        image_url = storage.get_url(object_key)

        if annotated_bytes:
            annotated_filename = f"annotated_{file.filename or 'leaf.jpg'}"
            annotated_object_key = storage.upload_image(
                annotated_bytes,
                filename=annotated_filename,
                content_type="image/jpeg",
            )
            annotated_image_url = storage.get_url(annotated_object_key)

        db_recommendation = dict(recommendation) if recommendation else {}
        db_recommendation["is_valid_leaf"] = domain_check.is_valid_leaf
        if domain_check.reason:
            db_recommendation["domain_warning"] = domain_check.reason
        if domain_check.reason_en:
            db_recommendation["domain_warning_en"] = domain_check.reason_en
        if annotated_object_key:
            db_recommendation["annotated_object_key"] = annotated_object_key
        if detections:
            db_recommendation["detections"] = detections
        image = crud.create_image_record(
            session=session,
            object_key=object_key,
            user_id=current_user.id if (current_user and hasattr(current_user, "id")) else None,
            original_filename=file.filename,
            content_type=file.content_type,
            size_bytes=len(image_bytes),
            commit=False,
        )
        prediction_record = crud.create_prediction_record(
            session=session,
            image_id=image.id,
            user_id=current_user.id if (current_user and hasattr(current_user, "id")) else None,
            predicted_label=prediction,
            confidence=confidence,
            top_k=top_k_payload,
            recommendation=db_recommendation or recommendation,
            model_version=settings.MODEL_VERSION,
            latency_ms=latency_ms,
            commit=False,
        )
        session.commit()
    except Exception as exc:
        if session and hasattr(session, "rollback"):
            session.rollback()
        if object_key:
            try:
                storage.delete_image(object_key)
            except Exception as storage_exc:
                print(f"Warning: Failed to clean up orphaned image '{object_key}': {storage_exc}")
        if annotated_object_key:
            try:
                storage.delete_image(annotated_object_key)
            except Exception as storage_exc:
                print(f"Warning: Failed to clean up orphaned annotated image '{annotated_object_key}': {storage_exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Storage or database unavailable: {exc}",
        ) from exc
    try:
        session.refresh(image)
        session.refresh(prediction_record)
    except Exception as exc:
        print(f"Warning: Failed to refresh db instances post-commit: {exc}")
    gc.collect()
    return PredictionResponse(
        prediction=prediction,
        confidence=confidence,
        top_k=[TopKPrediction(**item) for item in top_k_payload],
        recommendation=recommendation,
        image_id=str(image.id),
        image_url=image_url,
        annotated_image_url=annotated_image_url,
        detections=[DetectionItem(**d) for d in detections],
        prediction_id=str(prediction_record.id),
        latency_ms=latency_ms,
        is_valid_leaf=domain_check.is_valid_leaf,
        domain_warning=domain_check.reason,
        domain_warning_en=domain_check.reason_en,
    )

@router.get("/images/{object_key:path}")
async def get_image_file(object_key: str):
    """Retrieve and stream image file directly from storage."""
    if not object_key or "/" in object_key or "\\" in object_key or ".." in object_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image object key",
        )

    storage = get_storage_service()
    try:
        data, content_type = storage.get_image(object_key)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image '{object_key}' not found: {exc}",
        ) from exc

    return Response(
        content=data,
        media_type=content_type,
        headers={
            "Cache-Control": "public, max-age=86400, immutable",
            "Content-Disposition": f'inline; filename="{object_key}"',
        },
    )
