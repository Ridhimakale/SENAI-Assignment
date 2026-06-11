from dataclasses import dataclass

from app.core.config import get_settings
from app.models.email import Email
from app.models.enums import ActionStatus, ActionType
from app.repositories.agent import AgentRepository
from app.services.rag.service import RagService
from app.services.web_intelligence.service import WebIntelligenceService


@dataclass
class AgentTools:
    repository: AgentRepository
    rag_service: RagService
    web_intelligence_service: WebIntelligenceService | None = None

    async def search_knowledge_base(self, query: str) -> dict:
        result = self.rag_service.search(query)
        return {
            "query": result.query,
            "results": [item.model_dump() for item in result.results],
        }

    async def get_thread_history(self, sender_email: str) -> dict:
        emails = await self.repository.get_thread_history(sender_email)
        return {
            "emails": [
                {
                    "id": email.id,
                    "subject": email.subject,
                    "body": email.body,
                    "timestamp": email.timestamp.isoformat(),
                    "category": email.category.value if email.category else None,
                    "urgency": email.urgency.value if email.urgency else None,
                }
                for email in emails
            ]
        }

    async def get_contact_profile(self, email: str) -> dict:
        contact = await self.repository.get_contact_profile(email)
        if contact is None:
            return {"found": False}
        return {
            "found": True,
            "email": contact.email,
            "name": contact.name,
            "company": contact.company,
            "status": contact.status.value,
            "vip_reason": contact.vip_reason,
            "account_value": float(contact.account_value or 0),
            "churn_risk_score": contact.churn_risk_score,
            "subscription_tier": contact.subscription_tier,
            "renewal_status": contact.renewal_status,
        }

    async def check_account_status(self, email: str) -> dict:
        profile = await self.get_contact_profile(email)
        if not profile.get("found"):
            return {"found": False}
        return {
            "found": True,
            "subscription_tier": profile.get("subscription_tier") or "Unknown",
            "renewal_status": profile.get("renewal_status") or "Unknown",
            "account_value": profile.get("account_value", 0),
            "churn_risk_score": profile.get("churn_risk_score", 0),
        }

    async def draft_reply(self, *, context: str, tone: str, policy_refs: list[str]) -> dict:
        refs = ", ".join(policy_refs) if policy_refs else "internal policy"
        settings = get_settings()
        if settings.groq_api_key:
            try:
                from openai import AsyncOpenAI

                client = AsyncOpenAI(
                    api_key=settings.groq_api_key,
                    base_url="https://api.groq.com/openai/v1",
                )
                response = await client.chat.completions.create(
                    model=settings.groq_model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You draft short, empathetic CRM replies. "
                                "Return only JSON with a single key named draft."
                            ),
                        },
                        {
                            "role": "user",
                            "content": (
                                f"Tone: {tone}\n"
                                f"Policy references: {refs}\n"
                                f"Context: {context[:2000]}\n"
                                "Write a safe holding reply that cites the policy references."
                            ),
                        },
                    ],
                    temperature=0,
                    response_format={"type": "json_object"},
                )
                import json

                content = response.choices[0].message.content or "{}"
                parsed = json.loads(content)
                draft = parsed.get("draft")
                if draft:
                    return {
                        "draft": draft,
                        "policy_refs": policy_refs,
                        "context_used": context[:500],
                        "model_name": settings.groq_model,
                        "provider": "groq",
                    }
            except Exception:
                pass
        return {
            "draft": (
                f"Tone: {tone}. Thanks for reaching out. We are reviewing this with the "
                f"appropriate team and will follow the guidance in {refs}."
            ),
            "policy_refs": policy_refs,
            "context_used": context[:500],
            "provider": "fallback",
        }

    async def escalate_to_human(
        self, *, email: Email, reason: str, priority: str, reasoning_log: list[dict]
    ) -> dict:
        action = await self.repository.create_action(
            email_id=email.id,
            action_type=ActionType.ESCALATE,
            reasoning_log=reasoning_log,
            proposed_content=reason,
            status=ActionStatus.EXECUTED,
            tool_name="escalate_to_human",
            tool_input={"reason": reason, "priority": priority},
            tool_output={"escalated": True},
        )
        await self.repository.mark_email_escalated(email)
        return {"action_id": action.id, "escalated": True, "priority": priority}

    async def create_internal_ticket(
        self, *, email: Email, title: str, body: str, assignee: str, priority: str
    ) -> dict:
        ticket = await self.repository.create_internal_ticket(
            email=email,
            title=title,
            body=body,
            assignee=assignee,
            priority=priority,
        )
        await self.repository.create_action(
            email_id=email.id,
            action_type=ActionType.TICKET_CREATED,
            reasoning_log=[],
            proposed_content=title,
            status=ActionStatus.EXECUTED,
            tool_name="create_internal_ticket",
            tool_input={"title": title, "assignee": assignee, "priority": priority},
            tool_output={"ticket_id": ticket.id},
        )
        return {"ticket_id": ticket.id, "status": ticket.status.value}

    async def flag_for_legal(self, *, email: Email, issue_type: str, reasoning_log: list[dict]) -> dict:
        action = await self.repository.create_action(
            email_id=email.id,
            action_type=ActionType.LEGAL_FLAG,
            reasoning_log=reasoning_log,
            proposed_content=issue_type,
            status=ActionStatus.EXECUTED,
            tool_name="flag_for_legal",
            tool_input={"issue_type": issue_type},
            tool_output={"legal_flagged": True},
        )
        return {"action_id": action.id, "legal_flagged": True}

    async def send_auto_reply(self, *, email: Email, draft_id: int) -> dict:
        return {
            "sent": False,
            "blocked": True,
            "reason": "Auto-send is blocked until the safety gate and approval workflow are complete.",
            "draft_id": draft_id,
        }

    async def scrape_public_sentiment(self, company_name: str) -> dict:
        if self.web_intelligence_service is None:
            return {
                "company": company_name,
                "status": "unavailable",
                "summary": "Web intelligence service is not configured.",
            }
        result = await self.web_intelligence_service.get_reputation(company_name)
        return result.model_dump(mode="json")
