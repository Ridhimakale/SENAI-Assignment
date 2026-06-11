from datetime import datetime

from pydantic import BaseModel, Field, PositiveFloat, PositiveInt


class EmailStreamSimulationRequest(BaseModel):
    source_path: str = Field(
        default="email-data-advanced.json",
        description="Path to the replay dataset JSON file.",
    )
    emails_per_second: PositiveFloat = Field(
        default=1.0,
        description="Replay speed. Higher values mean shorter delays between emails.",
    )
    start_index: int = Field(
        default=0,
        ge=0,
        description="Zero-based index to start replaying from.",
    )
    limit: PositiveInt | None = Field(
        default=None,
        description="Optional maximum number of emails to replay.",
    )
    fail_fast: bool = Field(
        default=False,
        description="Stop replaying as soon as one email fails to ingest.",
    )
    dry_run: bool = Field(
        default=False,
        description="Load and normalize the dataset without ingesting emails.",
    )


class EmailStreamSimulationItem(BaseModel):
    index: int
    message_id: str
    thread_id: str
    sender: str
    timestamp: datetime
    status: str
    deduplicated: bool
    job_id: str | None
    email_id: int | None
    error: str | None = None


class EmailStreamSimulationResponse(BaseModel):
    source_path: str
    total_loaded: int
    processed: int
    succeeded: int
    failed: int
    deduplicated: int
    elapsed_seconds: float
    replay_rate_per_second: float
    results: list[EmailStreamSimulationItem]
