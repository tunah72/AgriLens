"""
Pydantic Schemas — Request/Response models.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# --- Prediction Schemas ---


class TopKPrediction(BaseModel):
    label: str
    confidence: float


class KnowledgeSource(BaseModel):
    title: str
    url: str


class DiseaseRecommendation(BaseModel):
    label: str | None = None
    crop: str | None = None
    name_vi: str
    name_en: str
    description: str | None = None
    description_vi: str | None = None
    symptoms: list[str] = Field(default_factory=list)
    symptoms_vi: list[str] = Field(default_factory=list)
    causes: list[str] = Field(default_factory=list)
    causes_vi: list[str] = Field(default_factory=list)
    treatments: list[str] = Field(default_factory=list)
    treatments_vi: list[str] = Field(default_factory=list)
    prevention: list[str] = Field(default_factory=list)
    prevention_vi: list[str] = Field(default_factory=list)
    severity: str | None = None
    sources: list[KnowledgeSource] = Field(default_factory=list)
    confidence: float | None = None
    confidence_note: str | None = None
    confidence_note_vi: str | None = None
    advisory: str | None = None
    advisory_vi: str | None = None


class KnowledgeListResponse(BaseModel):
    items: list[DiseaseRecommendation]
    total: int


class DetectionItem(BaseModel):
    label: str
    confidence: float
    box: list[float]
    class_id: int
    polygon: list[list[int]] | None = None
    polygons: list[list[list[int]]] = Field(default_factory=list)
    area_pct: float | None = None


class PredictionResponse(BaseModel):
    prediction: str
    confidence: float
    top_k: list[TopKPrediction]
    recommendation: DiseaseRecommendation | None = None
    image_id: str | None = None
    image_url: str | None = None
    annotated_image_url: str | None = None
    detections: list[DetectionItem] = Field(default_factory=list)
    prediction_id: str | None = None
    latency_ms: float | None = None

# --- User & Auth Schemas ---


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, examples=["farmer_john"])
    email: str = Field(..., examples=["john@example.com"])
    password: str = Field(..., min_length=6, examples=["secretpass"])


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    is_active: bool
    created_at: datetime


class LoginRequest(BaseModel):
    username: str = Field(..., examples=["farmer_john"])
    password: str = Field(..., examples=["secretpass"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- History Schemas ---


class HistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    image_id: str
    predicted_label: str
    confidence: float
    top_k: list[TopKPrediction]
    recommendation: DiseaseRecommendation | None = None
    image_url: str | None = None
    annotated_image_url: str | None = None
    detections: list[DetectionItem] = Field(default_factory=list)
    created_at: datetime


class HistoryResponse(BaseModel):
    items: list[HistoryItem]
    total: int
    page: int
    page_size: int
