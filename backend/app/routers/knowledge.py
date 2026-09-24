"""Knowledge base API routes."""

from fastapi import APIRouter, HTTPException

from backend.app.config import settings
from backend.app.knowledge import KnowledgeBase
from backend.app.models.schemas import DiseaseRecommendation, KnowledgeListResponse
from backend.app.services.cache import get_cache_service

router = APIRouter(prefix="/knowledge", tags=["knowledge"])
knowledge_base = KnowledgeBase()


@router.get("", response_model=KnowledgeListResponse)
async def list_knowledge() -> KnowledgeListResponse:
    """List supported plant disease labels and compact metadata with Redis caching."""
    cache = get_cache_service()
    cache_key = "knowledge:diseases:list"
    cached = cache.get_json(cache_key)
    if cached is not None:
        return KnowledgeListResponse(**cached)

    items = knowledge_base.list_diseases()
    response = KnowledgeListResponse(items=items, total=len(items))
    cache.set_json(cache_key, response.model_dump(), expire=settings.KNOWLEDGE_CACHE_TTL_SECONDS)
    return response

@router.get("/{disease_label}", response_model=DiseaseRecommendation)
async def get_knowledge(disease_label: str) -> DiseaseRecommendation:
    """Get detailed agricultural disease recommendations for a disease label with Redis caching."""
    cache = get_cache_service()
    cache_key = f"knowledge:disease:{disease_label.lower()}"
    cached = cache.get_json(cache_key)
    if cached is not None:
        return DiseaseRecommendation(**cached)

    disease = knowledge_base.get_disease_info(disease_label)
    if disease is None:
        raise HTTPException(status_code=404, detail=f"Unknown disease label: {disease_label}")
    rec = DiseaseRecommendation(**disease)
    cache.set_json(cache_key, rec.model_dump(), expire=settings.KNOWLEDGE_CACHE_TTL_SECONDS)
    return rec
