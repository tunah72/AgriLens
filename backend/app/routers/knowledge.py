"""Knowledge base API routes."""

from fastapi import APIRouter, HTTPException

from backend.app.knowledge import KnowledgeBase
from backend.app.models.schemas import DiseaseRecommendation, KnowledgeListResponse

router = APIRouter(prefix="/knowledge", tags=["knowledge"])
knowledge_base = KnowledgeBase()


@router.get("", response_model=KnowledgeListResponse)
async def list_knowledge() -> KnowledgeListResponse:
    """List supported plant disease labels and compact metadata."""
    items = knowledge_base.list_diseases()
    return KnowledgeListResponse(items=items, total=len(items))


@router.get("/{disease_label}", response_model=DiseaseRecommendation)
async def get_knowledge(disease_label: str) -> DiseaseRecommendation:
    """Get detailed agricultural disease recommendations for a disease label."""
    disease = knowledge_base.get_disease_info(disease_label)
    if disease is None:
        raise HTTPException(status_code=404, detail=f"Unknown disease label: {disease_label}")
    return DiseaseRecommendation(**disease)
