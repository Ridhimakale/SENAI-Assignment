from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action import Action
from app.models.contact import Contact
from app.models.email import Email
from app.models.enums import ActionStatus
from app.repositories.audit import AuditRepository
from app.repositories.operations import OperationsRepository
from app.schemas.operations import (
    ActionSummaryResponse,
    AuditLogResponse,
    ContactProfileResponse,
    ContactStatusUpdateRequest,
    ContactThreadsResponse,
    DashboardStatsResponse,
    EmailThreadItemResponse,
    ThreadDetailResponse,
)


class OperationsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = OperationsRepository(session)
        self.audit_repository = AuditRepository(session)

    async def get_dashboard_stats(self) -> DashboardStatsResponse:
        return DashboardStatsResponse(**await self.repository.dashboard_stats())

    async def get_threads_for_contact(self, contact_email: str) -> ContactThreadsResponse | None:
        contact = await self.repository.get_contact_with_threads(contact_email)
        if contact is None:
            return None

        open_threads = await self.repository.get_open_thread_count(contact.id)
        contact_response = self._contact_response(contact, open_threads=open_threads)
        threads = []
        for thread in self.repository.order_threads(contact.threads):
            ordered_emails = self.repository.order_emails(thread.emails)
            emails = []
            for email in ordered_emails:
                actions = [ActionSummaryResponse.model_validate(action) for action in email.actions]
                email_response = EmailThreadItemResponse.model_validate(email)
                email_response.actions = actions
                emails.append(email_response)
            thread_response = ThreadDetailResponse.model_validate(thread)
            thread_response.emails = emails
            thread_response.executive_summary = _build_executive_summary(thread.subject, ordered_emails, thread.status)
            threads.append(thread_response)
        return ContactThreadsResponse(contact=contact_response, threads=threads)

    async def get_contact_profile(self, email: str) -> ContactProfileResponse | None:
        contact = await self.repository.get_contact(email)
        if contact is None:
            return None
        return self._contact_response(
            contact,
            open_threads=await self.repository.get_open_thread_count(contact.id),
        )

    async def send_manual_reply(self, email_id: int, body: str, sender: str) -> Action | None:
        email = await self.repository.get_email(email_id)
        if email is None:
            return None
        action = await self.repository.create_manual_reply(email, body, sender)
        await self.audit_repository.create_event(
            entity_type="email",
            entity_id=email.id,
            action="REPLY_SENT",
            performed_by=sender,
            diff={"status": "Replied", "action_id": action.id},
        )
        await self.session.commit()
        return action

    async def update_draft(self, draft_id: int, proposed_content: str) -> Action | None:
        action = await self.repository.get_action(draft_id)
        if action is None:
            return None
        previous_content = action.proposed_content
        action = await self.repository.update_draft(action, proposed_content)
        await self.audit_repository.create_event(
            entity_type="action",
            entity_id=action.id,
            action="DRAFT_EDITED",
            performed_by="user",
            diff={"before": previous_content, "after": proposed_content},
        )
        await self.session.commit()
        return action

    async def approve_draft(self, draft_id: int, approved_by: str) -> Action | None:
        action = await self.repository.get_action(draft_id)
        if action is None:
            return None
        if action.status == ActionStatus.BLOCKED or action.safety_block_reason:
            raise ValueError(action.safety_block_reason or "Draft is blocked by safety rules.")
        action = await self.repository.approve_draft(action, approved_by)
        await self.audit_repository.create_event(
            entity_type="action",
            entity_id=action.id,
            action="DRAFT_APPROVED",
            performed_by=approved_by,
            diff={"email_id": action.email_id, "status": "Executed"},
        )
        if action.email:
            await self.audit_repository.create_event(
                entity_type="email",
                entity_id=action.email.id,
                action="REPLY_SENT",
                performed_by=approved_by,
                diff={"action_id": action.id},
            )
        await self.session.commit()
        return action

    async def get_audit_history(self, entity_type: str, entity_id: int) -> list[AuditLogResponse]:
        events = await self.repository.audit_history(entity_type, entity_id)
        return [AuditLogResponse.model_validate(event) for event in events]

    async def update_contact_status(
        self,
        email: str,
        request: ContactStatusUpdateRequest,
    ) -> ContactProfileResponse | None:
        contact = await self.repository.get_contact(email)
        if contact is None:
            return None
        old_status = contact.status
        old_vip_reason = contact.vip_reason
        contact = await self.repository.update_contact_status(
            contact,
            status=request.status,
            vip_reason=request.vip_reason,
        )
        await self.audit_repository.create_event(
            entity_type="contact",
            entity_id=contact.id,
            action="CONTACT_STATUS_UPDATED",
            performed_by="user",
            diff={
                "status": {"before": old_status, "after": request.status},
                "vip_reason": {"before": old_vip_reason, "after": contact.vip_reason},
            },
        )
        await self.session.commit()
        return self._contact_response(
            contact,
            open_threads=await self.repository.get_open_thread_count(contact.id),
        )

    @staticmethod
    def _contact_response(contact: Contact, *, open_threads: int) -> ContactProfileResponse:
        response = ContactProfileResponse.model_validate(contact)
        response.open_threads = open_threads
        return response


def _build_executive_summary(subject: str | None, emails: list[Email], status: object) -> str | None:
    if not emails:
        return None

    message_count = len(emails)
    first_email = emails[0]
    latest_email = emails[-1]
    status_value = getattr(status, "value", str(status))
    first_sentence = (
        f"This thread started with {first_email.subject or subject or 'an email'} and has now grown into a {message_count}-message conversation."
    )
    second_sentence = (
        f"The latest message focuses on {latest_email.subject or 'the current issue'} and the thread is currently {str(status_value).lower()}."
    )

    if message_count >= 5:
        middle_points = []
        if any((email.sentiment_score or 0) < -0.2 for email in emails):
            middle_points.append("sentiment has deteriorated over time")
        if any("legal" in f"{email.subject or ''} {email.body}".lower() for email in emails):
            middle_points.append("legal sensitivity is present")
        if any("refund" in f"{email.subject or ''} {email.body}".lower() for email in emails):
            middle_points.append("refund and retention context matters")
        if not middle_points:
            middle_points.append("the thread needs policy-aware handling")
        third_sentence = f"Key signals include {', '.join(middle_points)}."
    else:
        third_sentence = "No additional escalation pattern is visible yet, but the thread should be monitored closely."

    return " ".join([first_sentence, second_sentence, third_sentence])
