from datetime import datetime

from pydantic import BaseModel, Field


class ReputationSource(BaseModel):
    source: str
    source_url: str
    rating: float | None = None
    recent_review_count: int | None = None
    common_themes: list[str] = Field(default_factory=list)
    cached: bool = False
    status: str
    error_message: str | None = None
    robots_allowed: bool | None = None
    expires_at: datetime | None = None


class ReputationResponse(BaseModel):
    company: str
    sources: list[ReputationSource]
    summary: str
    market_intelligence_block: str


class WebIntelligenceTriggerResult(BaseModel):
    triggered: bool
    reasons: list[str] = Field(default_factory=list)
