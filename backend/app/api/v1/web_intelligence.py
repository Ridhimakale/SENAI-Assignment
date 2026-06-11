from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.common import ApiResponse
from app.schemas.web_intelligence import ReputationResponse
from app.services.web_intelligence.service import (
    WebIntelligenceService,
    create_web_intelligence_service,
)

router = APIRouter(prefix="/intelligence", tags=["web-intelligence"])


def get_web_intelligence_service(
    session: AsyncSession = Depends(get_db_session),
) -> WebIntelligenceService:
    return create_web_intelligence_service(session)


@router.get("/reputation", response_model=ApiResponse[ReputationResponse])
async def get_reputation(
    company: str = Query(..., min_length=1),
    service: WebIntelligenceService = Depends(get_web_intelligence_service),
) -> ApiResponse[ReputationResponse]:
    return ApiResponse(data=await service.get_reputation(company))
