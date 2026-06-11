from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import error_response
from app.db.session import get_db_session
from app.schemas.common import ApiResponse
from app.schemas.ingestion import EmailIngestRequest, EmailIngestResponse, ProcessingStatusResponse
from app.services.ingestion.service import IngestionService

router = APIRouter(prefix="/api", tags=["ingestion"])


def get_ingestion_service(
    session: AsyncSession = Depends(get_db_session),
) -> IngestionService:
    return IngestionService(session=session)


@router.post("/ingest", response_model=ApiResponse[EmailIngestResponse])
async def ingest_email(
    request: EmailIngestRequest,
    service: IngestionService = Depends(get_ingestion_service),
) -> ApiResponse[EmailIngestResponse]:
    result = await service.ingest_email(request)
    return ApiResponse(data=result)


@router.get("/status/{job_id}", response_model=ApiResponse[ProcessingStatusResponse])
async def get_processing_status(
    job_id: str,
    service: IngestionService = Depends(get_ingestion_service),
) -> ApiResponse[ProcessingStatusResponse]:
    result = await service.get_status(job_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                "JOB_NOT_FOUND",
                "Processing job was not found.",
                {"job_id": job_id},
            )["error"],
        )
    return ApiResponse(data=result)
