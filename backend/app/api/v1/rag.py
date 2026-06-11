from fastapi import APIRouter, Depends, Query

from app.schemas.common import ApiResponse
from app.schemas.rag import RagSearchResponse
from app.services.rag.service import RagService, get_rag_service

router = APIRouter(prefix="/rag", tags=["rag"])


@router.get("/search", response_model=ApiResponse[RagSearchResponse])
async def search_knowledge_base(
    q: str = Query(..., min_length=1),
    service: RagService = Depends(get_rag_service),
) -> ApiResponse[RagSearchResponse]:
    return ApiResponse(data=service.search(q))
