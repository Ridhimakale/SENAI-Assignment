from pydantic import BaseModel, Field, model_validator

from app.models.enums import EmailCategory, EmailUrgency


class DetectedEntities(BaseModel):
    order_ids: list[str] = Field(default_factory=list)
    ticket_ids: list[str] = Field(default_factory=list)
    monetary_amounts: list[str] = Field(default_factory=list)
    deadlines: list[str] = Field(default_factory=list)
    products_mentioned: list[str] = Field(default_factory=list)


class ClassificationOutput(BaseModel):
    category: EmailCategory
    sentiment: str = Field(pattern="^(Positive|Neutral|Negative|Mixed)$")
    sentiment_score: float = Field(ge=-1.0, le=1.0)
    urgency: EmailUrgency
    requires_human: bool
    escalation_reason: str | None
    suggested_reply: str | None
    confidence: float = Field(ge=0.0, le=1.0)
    detected_entities: DetectedEntities = Field(default_factory=DetectedEntities)

    @model_validator(mode="after")
    def validate_human_reply_fields(self) -> "ClassificationOutput":
        if self.requires_human and not self.escalation_reason:
            raise ValueError("escalation_reason is required when requires_human is true")
        if not self.requires_human and not self.suggested_reply:
            raise ValueError("suggested_reply is required when requires_human is false")
        return self


class ClassificationResponse(BaseModel):
    email_id: int
    classification: ClassificationOutput
    rag_sources: list[str]
    prompt_version: str
    model_name: str
    validation_status: str
