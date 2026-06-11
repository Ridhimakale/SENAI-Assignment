from datetime import UTC, datetime, time, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.analytics import (
    AgentPerformanceResponse,
    AtRiskAccountsResponse,
    CategoryBreakdownResponse,
    ResponseHeatmapResponse,
    SentimentTrendResponse,
)
from app.schemas.common import ApiResponse
from app.services.analytics.service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


def get_analytics_service(
    session: AsyncSession = Depends(get_db_session),
) -> AnalyticsService:
    return AnalyticsService(session=session)


@router.get("/sentiment-trend", response_model=ApiResponse[SentimentTrendResponse])
async def sentiment_trend(
    sender: str | None = None,
    days: int = Query(30, ge=1, le=365),
    service: AnalyticsService = Depends(get_analytics_service),
) -> ApiResponse[SentimentTrendResponse]:
    return ApiResponse(data=await service.sentiment_trend(sender=sender, days=days))


@router.get("/category-breakdown", response_model=ApiResponse[CategoryBreakdownResponse])
async def category_breakdown(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    service: AnalyticsService = Depends(get_analytics_service),
) -> ApiResponse[CategoryBreakdownResponse]:
    start, end = _date_range(start_date, end_date)
    return ApiResponse(data=await service.category_breakdown(start_date=start, end_date=end))


@router.get("/response-heatmap", response_model=ApiResponse[ResponseHeatmapResponse])
async def response_heatmap(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    service: AnalyticsService = Depends(get_analytics_service),
) -> ApiResponse[ResponseHeatmapResponse]:
    start, end = _date_range(start_date, end_date)
    return ApiResponse(data=await service.response_heatmap(start_date=start, end_date=end))


@router.get("/at-risk-accounts", response_model=ApiResponse[AtRiskAccountsResponse])
async def at_risk_accounts(
    service: AnalyticsService = Depends(get_analytics_service),
) -> ApiResponse[AtRiskAccountsResponse]:
    return ApiResponse(data=await service.at_risk_accounts())


@router.get("/agent-performance", response_model=ApiResponse[AgentPerformanceResponse])
async def agent_performance(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    service: AnalyticsService = Depends(get_analytics_service),
) -> ApiResponse[AgentPerformanceResponse]:
    start, end = _date_range(start_date, end_date)
    return ApiResponse(data=await service.agent_performance(start_date=start, end_date=end))


def _date_range(
    start_date: datetime | None, end_date: datetime | None
) -> tuple[datetime, datetime]:
    end = end_date or datetime.now(UTC)
    start = start_date or end - timedelta(days=30)
    return _as_utc(start), _as_utc(end)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
