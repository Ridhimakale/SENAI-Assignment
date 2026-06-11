from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.internal_ticket import InternalTicket
from app.models.contact import Contact
from app.models.action import Action
from app.models.email import Email
from app.models.enums import (
    ActionStatus,
    ActionType,
    EmailStatus,
    JobStatus,
    ThreadStatus,
    TicketStatus,
)
from app.models.processing_job import ProcessingJob
from app.models.thread import Thread


class IngestionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def find_email_with_job(self, message_id: str) -> tuple[Email, ProcessingJob | None] | None:
        result = await self.session.execute(
            select(Email, ProcessingJob)
            .outerjoin(ProcessingJob, Email.processing_job_id == ProcessingJob.id)
            .where(Email.message_id == message_id)
        )
        row = result.one_or_none()
        if row is None:
            return None
        return row[0], row[1]

    async def create_processing_job(self) -> ProcessingJob:
        job = ProcessingJob(
            job_id=f"job_{uuid4().hex}",
            status=JobStatus.QUEUED,
            stage="INGESTED",
        )
        self.session.add(job)
        await self.session.flush()
        return job

    async def get_or_create_contact(self, sender: str, timestamp: datetime) -> Contact:
        result = await self.session.execute(select(Contact).where(Contact.email == sender))
        contact = result.scalar_one_or_none()
        if contact is not None:
            contact.last_contact_at = _max_datetime(contact.last_contact_at, timestamp)
            return contact

        contact = Contact(
            email=sender,
            name=_guess_name_from_email(sender),
            company=_guess_company_from_email(sender),
            last_contact_at=timestamp,
        )
        self.session.add(contact)
        await self.session.flush()
        return contact

    async def get_contact_emails(self, contact_id: int) -> list[Email]:
        result = await self.session.execute(
            select(Email)
            .where(Email.contact_id == contact_id)
            .order_by(Email.timestamp.asc())
        )
        return list(result.scalars().all())

    async def count_open_tickets_for_contact(self, contact_id: int) -> int:
        result = await self.session.execute(
            select(InternalTicket)
            .join(Email, InternalTicket.email_id == Email.id)
            .where(
                Email.contact_id == contact_id,
                InternalTicket.status != TicketStatus.RESOLVED,
            )
        )
        return len(list(result.scalars().all()))

    async def update_contact_profile(
        self,
        contact: Contact,
        *,
        account_value,
        churn_risk_score: float,
        subscription_tier: str | None,
        renewal_status: str | None,
        vip_reason: str | None,
        status,
        metadata_json: dict,
        open_ticket_count: int,
    ) -> Contact:
        contact.account_value = account_value
        contact.churn_risk_score = churn_risk_score
        contact.subscription_tier = subscription_tier
        contact.renewal_status = renewal_status
        contact.vip_reason = vip_reason
        contact.status = status
        contact.metadata_json = {
            **(contact.metadata_json or {}),
            **metadata_json,
        }
        contact.open_ticket_count = open_ticket_count
        await self.session.flush()
        return contact

    async def get_or_create_thread(
        self,
        *,
        external_thread_id: str,
        contact: Contact,
        sender: str,
        subject: str | None,
        timestamp: datetime,
    ) -> Thread:
        result = await self.session.execute(
            select(Thread).where(
                Thread.thread_id == external_thread_id,
                Thread.sender_email == sender,
            )
        )
        thread = result.scalar_one_or_none()
        if thread is not None:
            thread.first_seen_at = _min_datetime(thread.first_seen_at, timestamp)
            thread.last_updated_at = _max_datetime(thread.last_updated_at, timestamp)
            if subject and not thread.subject:
                thread.subject = subject
            return thread

        thread = Thread(
            thread_id=external_thread_id,
            contact_id=contact.id,
            subject=subject,
            sender_email=sender,
            first_seen_at=timestamp,
            last_updated_at=timestamp,
            status=ThreadStatus.OPEN,
        )
        self.session.add(thread)
        await self.session.flush()
        return thread

    async def create_email(
        self,
        *,
        thread: Thread,
        contact: Contact,
        job: ProcessingJob,
        message_id: str,
        sender: str,
        subject: str,
        normalized_subject: str,
        body: str,
        body_preview: str,
        body_truncated: bool,
        timestamp: datetime,
        priority_score: int,
        heuristic_flags: dict,
    ) -> Email:
        email = Email(
            thread_id=thread.id,
            contact_id=contact.id,
            processing_job_id=job.id,
            message_id=message_id,
            sender=sender,
            subject=subject,
            normalized_subject=normalized_subject,
            body=body,
            body_preview=body_preview,
            body_truncated=body_truncated,
            timestamp=timestamp,
            status=EmailStatus.RECEIVED,
            priority_score=priority_score,
            heuristic_flags=heuristic_flags,
        )
        self.session.add(email)
        await self.session.flush()
        job.email = email
        return email

    async def update_thread_after_email(
        self, *, thread: Thread, timestamp: datetime, priority_score: int
    ) -> None:
        thread.message_count += 1
        thread.first_seen_at = _min_datetime(thread.first_seen_at, timestamp)
        thread.last_updated_at = _max_datetime(thread.last_updated_at, timestamp)
        thread.priority_score = max(thread.priority_score, priority_score)
        await self.session.flush()

    async def create_triage_action(
        self,
        *,
        email: Email,
        action_type: ActionType,
        reason: str,
        status: ActionStatus = ActionStatus.EXECUTED,
    ) -> Action:
        action = Action(
            email_id=email.id,
            action_type=action_type,
            status=status,
            agent_reasoning_log=[
                {
                    "thought": "A deterministic heuristic rule matched during ingestion.",
                    "action": action_type.value,
                    "observation": reason,
                    "next_step": "Stop processing or wait for the next safe pipeline stage.",
                }
            ],
            proposed_content=reason,
            is_approved=False,
            tool_name="heuristic_prefilter",
            tool_input=email.heuristic_flags,
            tool_output={"reason": reason},
        )
        self.session.add(action)
        await self.session.flush()
        return action

    async def get_processing_job_by_job_id(self, job_id: str) -> ProcessingJob | None:
        result = await self.session.execute(
            select(ProcessingJob)
            .options(selectinload(ProcessingJob.email))
            .where(ProcessingJob.job_id == job_id)
        )
        return result.scalar_one_or_none()


def _guess_name_from_email(email: str) -> str:
    local_part = email.split("@", 1)[0]
    return " ".join(part.capitalize() for part in local_part.replace(".", " ").split())


def _guess_company_from_email(email: str) -> str | None:
    if "@" not in email:
        return None
    domain = email.split("@", 1)[1].split(".", 1)[0]
    return domain.replace("-", " ").title()


def _min_datetime(left: datetime | None, right: datetime) -> datetime:
    if left is None:
        return right
    return min(_as_utc(left), _as_utc(right))


def _max_datetime(left: datetime | None, right: datetime) -> datetime:
    if left is None:
        return right
    return max(_as_utc(left), _as_utc(right))


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
