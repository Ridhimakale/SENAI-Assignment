from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import error_response
from app.db.session import get_db_session
from app.schemas.common import ApiResponse
from app.schemas.simulation import EmailStreamSimulationRequest, EmailStreamSimulationResponse
from app.services.ingestion.service import IngestionService
from app.services.simulation.service import EmailStreamSimulatorService

router = APIRouter(prefix="/api", tags=["simulation"])


def get_simulation_service(
    session: AsyncSession = Depends(get_db_session),
) -> EmailStreamSimulatorService:
    return EmailStreamSimulatorService(ingestion_service=IngestionService(session=session))


@router.post("/simulate/stream", response_model=ApiResponse[EmailStreamSimulationResponse])
async def simulate_email_stream(
    request: EmailStreamSimulationRequest,
    service: EmailStreamSimulatorService = Depends(get_simulation_service),
) -> ApiResponse[EmailStreamSimulationResponse]:
    try:
        result = await service.run(request)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                "DATASET_NOT_FOUND",
                str(exc),
                {"source_path": request.source_path},
            )["error"],
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response(
                "SIMULATION_DATA_ERROR",
                str(exc),
                {"source_path": request.source_path},
            )["error"],
        ) from exc
    return ApiResponse(data=result)
