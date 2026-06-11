from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import error_response
from app.db.session import get_db_session
from app.schemas.classification import ClassificationResponse
from app.schemas.common import ApiResponse
from app.services.intelligence.classification_service import (
    ClassificationService,
    create_classification_service,
)

router = APIRouter(prefix="/api", tags=["classification"])


def get_classification_service(
    session: AsyncSession = Depends(get_db_session),
) -> ClassificationService:
    return create_classification_service(session)


@router.post("/classify/{email_id}", response_model=ApiResponse[ClassificationResponse])
async def classify_email(
    email_id: int,
    service: ClassificationService = Depends(get_classification_service),
) -> ApiResponse[ClassificationResponse]:
    try:
        return ApiResponse(data=await service.classify_email(email_id))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                "CLASSIFICATION_NOT_ALLOWED",
                str(exc),
                {"email_id": email_id},
            )["error"],
        ) from exc
