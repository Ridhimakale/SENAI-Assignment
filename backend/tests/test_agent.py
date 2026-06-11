from datetime import UTC, datetime

import pytest

import app.db.base  # noqa: F401
from app.models.email import Email
from app.models.enums import EmailCategory, EmailUrgency
from app.schemas.rag import RagSearchResponse, RagSearchResult
from app.services.agents.safety import auto_reply_block_reason
from app.services.agents import react_service
from app.services.agents.react_service import ReActAgentService


def test_auto_reply_blocks_critical_email() -> None:
    email = Email(
        id=1,
        thread_id=1,
        contact_id=1,
        message_id="msg_critical",
        sender="bob@example.com",
        body="Legal escalation",
        timestamp="2026-01-01T00:00:00Z",
        urgency=EmailUrgency.CRITICAL,
    )

    assert auto_reply_block_reason(email) == "Auto-reply blocked for critical urgency."


def test_auto_reply_blocks_legal_email() -> None:
    email = Email(
        id=1,
        thread_id=1,
        contact_id=1,
        message_id="msg_legal",
        sender="legal@example.com",
        body="Cease and desist",
        timestamp="2026-01-01T00:00:00Z",
        category=EmailCategory.LEGAL,
    )

    assert auto_reply_block_reason(email) == "Auto-reply blocked for legal matters."


def test_auto_reply_allows_safe_non_human_email() -> None:
    email = Email(
        id=1,
        thread_id=1,
        contact_id=1,
        message_id="msg_safe",
        sender="alice@example.com",
        body="Billing question",
        timestamp="2026-01-01T00:00:00Z",
        category=EmailCategory.BILLING,
        urgency=EmailUrgency.LOW,
        requires_human=False,
    )

    assert auto_reply_block_reason(email) is None


class FakeAgentRepository:
    def __init__(self, session):
        self.email = Email(
            id=60,
            thread_id=1,
            contact_id=1,
            message_id="msg_060",
            sender="bob.jones@enterprise.net",
            subject="Escalation: SLA Breach + Legal Review",
            body="Our legal team is reviewing the SLA breach and RCA obligations.",
            timestamp=datetime(2026, 1, 14, tzinfo=UTC),
            category=EmailCategory.LEGAL,
            urgency=EmailUrgency.CRITICAL,
            requires_human=True,
            classification_raw={
                "escalation_reason": "SLA breach and legal review require human escalation."
            },
        )

    async def get_email_context(self, email_id: int):
        return self.email

    async def get_thread_history(self, sender_email: str):
        return [
            Email(
                id=index,
                thread_id=1,
                contact_id=1,
                message_id=f"msg_00{index}",
                sender=sender_email,
                subject="P0 outage update",
                body="We need RCA and SLA credit information.",
                timestamp=datetime(2026, 1, index, tzinfo=UTC),
            )
            for index in range(1, 5)
        ]

    async def get_contact_profile(self, email: str):
        return None


class FakeRagService:
    def search(self, query: str) -> RagSearchResponse:
        return RagSearchResponse(
            query=query,
            results=[
                RagSearchResult(
                    chunk_id="sla_policy.md:0",
                    source_doc="sla_policy.md",
                    chunk_index=0,
                    chunk_text="P0 incidents require RCA within 24 hours and SLA credits.",
                    score=0.91,
                )
            ],
        )


@pytest.mark.asyncio
async def test_bob_legal_sla_dry_run_follows_required_sequence(monkeypatch) -> None:
    monkeypatch.setattr(react_service, "AgentRepository", FakeAgentRepository)
    monkeypatch.setattr(react_service, "get_rag_service", lambda: FakeRagService())
    service = ReActAgentService(session=None, max_tool_calls=6)  # type: ignore[arg-type]

    result = await service.run(60, dry_run=True)

    assert result.tool_call_count == 6
    assert [step.action for step in result.reasoning_trace] == [
        "get_thread_history",
        "search_knowledge_base",
        "check_account_status",
        "flag_for_legal",
        "draft_reply",
        "escalate_to_human",
    ]
    assert [action.action_type for action in result.proposed_actions] == [
        "Legal-Flag",
        "Auto-Reply",
        "Escalate",
    ]
    assert result.proposed_actions[1].safety_block_reason == (
        "Auto-reply blocked for critical urgency."
    )
