from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import error_response
from app.db.session import get_db_session
from app.schemas.agent import AgentRunResponse, DraftGenerationResponse
from app.schemas.common import ApiResponse
from app.services.agents.react_service import ReActAgentService, create_react_agent_service

router = APIRouter(prefix="/agent", tags=["agent"])


def get_agent_service(
    session: AsyncSession = Depends(get_db_session),
) -> ReActAgentService:
    return create_react_agent_service(session)


@router.post("/dry-run/{email_id}", response_model=ApiResponse[AgentRunResponse])
async def dry_run_agent(
    email_id: int,
    service: ReActAgentService = Depends(get_agent_service),
) -> ApiResponse[AgentRunResponse]:
    try:
        return ApiResponse(data=await service.run(email_id, dry_run=True))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                "EMAIL_NOT_FOUND",
                str(exc),
                {"email_id": email_id},
            )["error"],
        ) from exc


@router.post("/draft/{email_id}", response_model=ApiResponse[DraftGenerationResponse])
async def generate_draft(
    email_id: int,
    service: ReActAgentService = Depends(get_agent_service),
) -> ApiResponse[DraftGenerationResponse]:
    try:
        return ApiResponse(data=await service.generate_draft(email_id))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                "EMAIL_NOT_FOUND",
                str(exc),
                {"email_id": email_id},
            )["error"],
        ) from exc
