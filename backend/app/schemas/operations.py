from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    ActionStatus,
    ActionType,
    ContactStatus,
    EmailCategory,
    EmailStatus,
    EmailUrgency,
    ThreadStatus,
)


class DashboardStatsResponse(BaseModel):
    pending: int
    replied: int
    escalated: int
    critical: int
    spam: int
    needs_human: int


class ContactProfileResponse(BaseModel):
    id: int
    email: str
    name: str | None
    company: str | None
    status: ContactStatus
    vip_reason: str | None
    account_value: Decimal | None
    churn_risk_score: float
    subscription_tier: str | None
    renewal_status: str | None
    open_ticket_count: int
    open_threads: int = 0
    last_contact_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class ActionSummaryResponse(BaseModel):
    id: int
    email_id: int
    action_type: ActionType
    status: ActionStatus
    proposed_content: str | None
    is_approved: bool
    approved_by: str | None
    executed_at: datetime | None
    safety_block_reason: str | None
    agent_reasoning_log: list | dict | None
    tool_name: str | None
    tool_input: dict | None
    tool_output: dict | None

    model_config = ConfigDict(from_attributes=True)


class EmailThreadItemResponse(BaseModel):
    id: int
    message_id: str
    sender: str
    subject: str | None
    body: str
    timestamp: datetime
    sentiment_score: float | None
    category: EmailCategory | None
    urgency: EmailUrgency | None
    requires_human: bool
    confidence: float | None
    raw_entities: dict | None
    status: EmailStatus
    priority_score: int
    heuristic_flags: dict | None
    rag_context: dict | None
    actions: list[ActionSummaryResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ThreadDetailResponse(BaseModel):
    id: int
    thread_id: str
    subject: str | None
    sender_email: str
    first_seen_at: datetime
    last_updated_at: datetime
    status: ThreadStatus
    assigned_to: str | None
    priority_score: int
    message_count: int
    executive_summary: str | None = None
    emails: list[EmailThreadItemResponse]

    model_config = ConfigDict(from_attributes=True)


class ContactThreadsResponse(BaseModel):
    contact: ContactProfileResponse
    threads: list[ThreadDetailResponse]


class ManualReplyRequest(BaseModel):
    body: str = Field(min_length=1)
    sender: str = Field(default="user")


class DraftUpdateRequest(BaseModel):
    proposed_content: str = Field(min_length=1)


class DraftApproveRequest(BaseModel):
    approved_by: str = Field(default="user")


class ContactStatusUpdateRequest(BaseModel):
    status: ContactStatus
    vip_reason: str | None = None


class AuditLogResponse(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    action: str
    performed_by: str
    timestamp: datetime
    diff: dict | None
    request_id: str | None
    correlation_id: str | None
    metadata_json: dict | None

    model_config = ConfigDict(from_attributes=True)
