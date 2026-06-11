from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.classification_run import ClassificationRun
from app.models.email import Email
from app.models.enums import (
    ClassificationValidationStatus,
    EmailCategory,
    EmailStatus,
    EmailUrgency,
    JobStatus,
)


class ClassificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_email_for_classification(self, email_id: int) -> Email | None:
        result = await self.session.execute(
            select(Email)
            .options(selectinload(Email.thread), selectinload(Email.processing_job))
            .where(Email.id == email_id)
        )
        return result.scalar_one_or_none()

    async def get_thread_history(self, email: Email) -> list[Email]:
        result = await self.session.execute(
            select(Email)
            .where(Email.thread_id == email.thread_id, Email.sender == email.sender)
            .order_by(Email.timestamp.asc())
        )
        return list(result.scalars().all())

    async def create_classification_run(
        self,
        *,
        email: Email,
        prompt_version: str,
        model_name: str,
        output: dict | None,
        confidence: float | None,
        validation_status: ClassificationValidationStatus,
        error_message: str | None = None,
    ) -> ClassificationRun:
        run = ClassificationRun(
            email_id=email.id,
            prompt_version=prompt_version,
            model_name=model_name,
            classification_output=output,
            confidence=confidence,
            validation_status=validation_status,
            error_message=error_message,
        )
        self.session.add(run)
        await self.session.flush()
        return run

    async def apply_classification(
        self,
        *,
        email: Email,
        output: dict,
        rag_context: dict,
        requires_human: bool,
    ) -> None:
        email.category = EmailCategory(output["category"])
        email.sentiment_score = output["sentiment_score"]
        email.urgency = EmailUrgency(output["urgency"])
        email.requires_human = requires_human
        email.confidence = output["confidence"]
        email.raw_entities = output["detected_entities"]
        email.classification_raw = output
        email.classification_error = None
        email.rag_context = rag_context
        email.status = EmailStatus.PROCESSING
        if email.processing_job:
            email.processing_job.stage = "CLASSIFIED"
            email.processing_job.status = JobStatus.PROCESSING
        await self.session.flush()
