from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.action import Action
from app.models.contact import Contact
from app.models.email import Email
from app.models.enums import ActionStatus, ActionType, EmailStatus, ThreadStatus
from app.models.internal_ticket import InternalTicket


class AgentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_email_context(self, email_id: int) -> Email | None:
        result = await self.session.execute(
            select(Email)
            .options(
                selectinload(Email.contact),
                selectinload(Email.thread),
                selectinload(Email.actions),
            )
            .where(Email.id == email_id)
        )
        return result.scalar_one_or_none()

    async def get_thread_history(self, sender_email: str) -> list[Email]:
        result = await self.session.execute(
            select(Email)
            .where(Email.sender == sender_email)
            .order_by(Email.timestamp.asc())
        )
        return list(result.scalars().all())

    async def get_contact_profile(self, email: str) -> Contact | None:
        result = await self.session.execute(select(Contact).where(Contact.email == email))
        return result.scalar_one_or_none()

    async def create_action(
        self,
        *,
        email_id: int,
        action_type: ActionType,
        reasoning_log: list[dict],
        proposed_content: str | None = None,
        status: ActionStatus = ActionStatus.PROPOSED,
        safety_block_reason: str | None = None,
        tool_name: str | None = None,
        tool_input: dict | None = None,
        tool_output: dict | None = None,
    ) -> Action:
        action = Action(
            email_id=email_id,
            action_type=action_type,
            agent_reasoning_log=reasoning_log,
            proposed_content=proposed_content,
            status=status,
            safety_block_reason=safety_block_reason,
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output=tool_output,
            is_approved=False,
        )
        self.session.add(action)
        await self.session.flush()
        return action

    async def create_internal_ticket(
        self,
        *,
        email: Email,
        title: str,
        body: str,
        assignee: str,
        priority: str,
    ) -> InternalTicket:
        ticket = InternalTicket(
            email_id=email.id,
            thread_id=email.thread_id,
            title=title,
            body=body,
            assignee=assignee,
            priority=priority,
        )
        self.session.add(ticket)
        await self.session.flush()
        return ticket

    async def mark_email_escalated(self, email: Email) -> None:
        email.status = EmailStatus.ESCALATED
        if email.thread:
            email.thread.status = ThreadStatus.ESCALATED
        await self.session.flush()
