from datetime import datetime

from pydantic import BaseModel


class SentimentTrendPoint(BaseModel):
    timestamp: datetime
    sender: str | None = None
    sentiment_score: float
    moving_average: float


class SentimentTrendResponse(BaseModel):
    sender: str | None
    points: list[SentimentTrendPoint]
    deterioration_detected: bool
    consecutive_negative_count: int


class CategoryBreakdownItem(BaseModel):
    category: str
    count: int


class CategoryBreakdownResponse(BaseModel):
    items: list[CategoryBreakdownItem]


class ResponseHeatmapPoint(BaseModel):
    hour_of_day: int
    action_count: int


class ResponseHeatmapResponse(BaseModel):
    points: list[ResponseHeatmapPoint]


class AtRiskAccount(BaseModel):
    sender: str
    company: str | None
    churn_risk_score: float
    unresolved_threads: int
    oldest_unresolved_hours: float | None
    consecutive_negative_count: int
    reasons: list[str]


class AtRiskAccountsResponse(BaseModel):
    accounts: list[AtRiskAccount]


class AgentPerformanceResponse(BaseModel):
    total_actions: int
    auto_reply_count: int
    escalation_count: int
    auto_reply_rate: float
    escalation_rate: float
    average_confidence_score: float | None
