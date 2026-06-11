from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import error_response
from app.db.session import get_db_session
from app.schemas.common import ApiResponse
from app.schemas.operations import (
    ActionSummaryResponse,
    AuditLogResponse,
    ContactProfileResponse,
    ContactStatusUpdateRequest,
    ContactThreadsResponse,
    DashboardStatsResponse,
    DraftApproveRequest,
    DraftUpdateRequest,
    ManualReplyRequest,
)
from app.services.operations.service import OperationsService

router = APIRouter(tags=["operations"])


def get_operations_service(
    session: AsyncSession = Depends(get_db_session),
) -> OperationsService:
    return OperationsService(session=session)


@router.get("/dashboard/stats", response_model=ApiResponse[DashboardStatsResponse])
async def get_dashboard_stats(
    service: OperationsService = Depends(get_operations_service),
) -> ApiResponse[DashboardStatsResponse]:
    return ApiResponse(data=await service.get_dashboard_stats())


@router.get("/threads/{contact_email}", response_model=ApiResponse[ContactThreadsResponse])
async def get_threads_for_contact(
    contact_email: str,
    service: OperationsService = Depends(get_operations_service),
) -> ApiResponse[ContactThreadsResponse]:
    result = await service.get_threads_for_contact(contact_email)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                "CONTACT_NOT_FOUND",
                "Contact was not found.",
                {"email": contact_email},
            )["error"],
        )
    return ApiResponse(data=result)


@router.post("/respond/{email_id}", response_model=ApiResponse[ActionSummaryResponse])
async def send_manual_reply(
    email_id: int,
    request: ManualReplyRequest,
    service: OperationsService = Depends(get_operations_service),
) -> ApiResponse[ActionSummaryResponse]:
    result = await service.send_manual_reply(email_id, request.body, request.sender)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                "EMAIL_NOT_FOUND",
                "Email was not found.",
                {"email_id": email_id},
            )["error"],
        )
    return ApiResponse(data=ActionSummaryResponse.model_validate(result))


@router.patch("/drafts/{draft_id}", response_model=ApiResponse[ActionSummaryResponse])
async def update_draft(
    draft_id: int,
    request: DraftUpdateRequest,
    service: OperationsService = Depends(get_operations_service),
) -> ApiResponse[ActionSummaryResponse]:
    result = await service.update_draft(draft_id, request.proposed_content)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                "DRAFT_NOT_FOUND",
                "Draft action was not found.",
                {"draft_id": draft_id},
            )["error"],
        )
    return ApiResponse(data=ActionSummaryResponse.model_validate(result))


@router.post("/drafts/{draft_id}/approve", response_model=ApiResponse[ActionSummaryResponse])
async def approve_draft(
    draft_id: int,
    request: DraftApproveRequest,
    service: OperationsService = Depends(get_operations_service),
) -> ApiResponse[ActionSummaryResponse]:
    try:
        result = await service.approve_draft(draft_id, request.approved_by)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_response(
                "DRAFT_BLOCKED",
                str(exc),
                {"draft_id": draft_id},
            )["error"],
        ) from exc
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                "DRAFT_NOT_FOUND",
                "Draft action was not found.",
                {"draft_id": draft_id},
            )["error"],
        )
    return ApiResponse(data=ActionSummaryResponse.model_validate(result))


@router.get("/audit/{entity_type}/{entity_id}", response_model=ApiResponse[list[AuditLogResponse]])
async def get_audit_history(
    entity_type: str,
    entity_id: int,
    service: OperationsService = Depends(get_operations_service),
) -> ApiResponse[list[AuditLogResponse]]:
    return ApiResponse(data=await service.get_audit_history(entity_type, entity_id))


@router.get("/contacts/{email}", response_model=ApiResponse[ContactProfileResponse])
async def get_contact_profile(
    email: str,
    service: OperationsService = Depends(get_operations_service),
) -> ApiResponse[ContactProfileResponse]:
    result = await service.get_contact_profile(email)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                "CONTACT_NOT_FOUND",
                "Contact was not found.",
                {"email": email},
            )["error"],
        )
    return ApiResponse(data=result)


@router.patch("/contacts/{email}/status", response_model=ApiResponse[ContactProfileResponse])
async def update_contact_status(
    email: str,
    request: ContactStatusUpdateRequest,
    service: OperationsService = Depends(get_operations_service),
) -> ApiResponse[ContactProfileResponse]:
    result = await service.update_contact_status(email, request)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                "CONTACT_NOT_FOUND",
                "Contact was not found.",
                {"email": email},
            )["error"],
        )
    return ApiResponse(data=result)
