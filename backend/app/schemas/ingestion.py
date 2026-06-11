from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class EmailIngestRequest(BaseModel):
    message_id: str
    thread_id: str
    sender: str
    subject: str | None = ""
    body: str | None = ""
    timestamp: datetime

    @field_validator("message_id", "thread_id", "sender")
    @classmethod
    def must_not_be_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Field cannot be blank.")
        return cleaned

    @field_validator("subject", "body", mode="before")
    @classmethod
    def default_optional_text(cls, value: object) -> str:
        if value is None:
            return ""
        return str(value)


class EmailIngestResponse(BaseModel):
    job_id: str
    email_id: int
    message_id: str
    deduplicated: bool
    status: str
    priority_score: int


class ProcessingStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: str
    email_id: int | None
    status: str
    stage: str
    error_code: str | None
    error_message: str | None
    updated_at: datetime
