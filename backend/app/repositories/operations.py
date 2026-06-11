from collections.abc import Iterable
from datetime import UTC, datetime

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.action import Action
from app.models.audit_log import AuditLog
from app.models.contact import Contact
from app.models.email import Email
from app.models.enums import ActionStatus, ActionType, EmailCategory, EmailStatus, EmailUrgency
from app.models.thread import Thread


class OperationsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def count_emails(self, statement: Select[tuple[Email]]) -> int:
        count_statement = select(func.count()).select_from(statement.subquery())
        return int(await self.session.scalar(count_statement) or 0)

    async def dashboard_stats(self) -> dict[str, int]:
        base = select(Email)
        return {
            "pending": await self.count_emails(
                base.where(Email.status.in_([EmailStatus.RECEIVED, EmailStatus.PROCESSING]))
            ),
            "replied": await self.count_emails(base.where(Email.status == EmailStatus.REPLIED)),
            "escalated": await self.count_emails(base.where(Email.status == EmailStatus.ESCALATED)),
            "critical": await self.count_emails(base.where(Email.urgency == EmailUrgency.CRITICAL)),
            "spam": await self.count_emails(base.where(Email.category == EmailCategory.SPAM)),
            "needs_human": await self.count_emails(base.where(Email.requires_human.is_(True))),
        }

    async def get_contact(self, email: str) -> Contact | None:
        return await self.session.scalar(select(Contact).where(Contact.email == email))

    async def get_contact_with_threads(self, email: str) -> Contact | None:
        return await self.session.scalar(
            select(Contact)
            .options(selectinload(Contact.threads).selectinload(Thread.emails).selectinload(Email.actions))
            .where(Contact.email == email)
        )

    async def get_open_thread_count(self, contact_id: int) -> int:
        return int(
            await self.session.scalar(
                select(func.count())
                .select_from(Thread)
                .where(Thread.contact_id == contact_id, Thread.status != "Resolved")
            )
            or 0
        )

    async def get_email(self, email_id: int) -> Email | None:
        return await self.session.scalar(
            select(Email)
            .options(selectinload(Email.thread), selectinload(Email.actions))
            .where(Email.id == email_id)
        )

    async def get_action(self, action_id: int) -> Action | None:
        return await self.session.scalar(
            select(Action)
            .options(selectinload(Action.email).selectinload(Email.thread))
            .where(Action.id == action_id)
        )

    async def create_manual_reply(self, email: Email, body: str, sender: str) -> Action:
        action = Action(
            email_id=email.id,
            action_type=ActionType.AUTO_REPLY,
            status=ActionStatus.EXECUTED,
            proposed_content=body,
            is_approved=True,
            approved_by=sender,
            executed_at=datetime.now(UTC),
            agent_reasoning_log=[
                {
                    "thought": "A human sent a manual reply from the dashboard.",
                    "action": "send_reply",
                    "observation": "Reply content was recorded and email marked replied.",
                    "next_step": "Audit the reply action.",
                }
            ],
        )
        self.session.add(action)
        email.status = EmailStatus.REPLIED
        if email.thread:
            email.thread.status = "Resolved"
        await self.session.flush()
        return action

    async def update_draft(self, action: Action, proposed_content: str) -> Action:
        action.proposed_content = proposed_content
        await self.session.flush()
        return action

    async def approve_draft(self, action: Action, approved_by: str) -> Action:
        action.is_approved = True
        action.approved_by = approved_by
        action.status = ActionStatus.EXECUTED
        action.executed_at = datetime.now(UTC)
        if action.email:
            action.email.status = EmailStatus.REPLIED
            if action.email.thread:
                action.email.thread.status = "Resolved"
        await self.session.flush()
        return action

    async def audit_history(self, entity_type: str, entity_id: int) -> list[AuditLog]:
        result = await self.session.scalars(
            select(AuditLog)
            .where(AuditLog.entity_type == entity_type, AuditLog.entity_id == entity_id)
            .order_by(AuditLog.timestamp.asc())
        )
        return list(result)

    async def update_contact_status(
        self,
        contact: Contact,
        *,
        status: str,
        vip_reason: str | None,
    ) -> Contact:
        contact.status = status
        if vip_reason is not None:
            contact.vip_reason = vip_reason
        await self.session.flush()
        return contact

    @staticmethod
    def order_threads(threads: Iterable[Thread]) -> list[Thread]:
        return sorted(threads, key=lambda thread: thread.last_updated_at, reverse=True)

    @staticmethod
    def order_emails(emails: Iterable[Email]) -> list[Email]:
        return sorted(emails, key=lambda email: email.timestamp)
