from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.email import Email
from app.models.enums import ActionStatus, ActionType, EmailCategory, EmailUrgency
from app.repositories.agent import AgentRepository
from app.schemas.agent import AgentRunResponse, ProposedAction, ReasoningStep
from app.services.agents.safety import auto_reply_block_reason
from app.services.rag.service import get_rag_service
from app.services.web_intelligence.service import create_web_intelligence_service
from app.services.web_intelligence.triggers import should_trigger_web_intelligence
from app.tools.agent_tools import AgentTools


@dataclass
class ReActAgentService:
    session: AsyncSession
    max_tool_calls: int

    async def run(self, email_id: int, *, dry_run: bool) -> AgentRunResponse:
        repository = AgentRepository(self.session)
        email = await repository.get_email_context(email_id)
        if email is None:
            raise ValueError("Email not found.")

        tools = AgentTools(
            repository=repository,
            rag_service=get_rag_service(),
            web_intelligence_service=create_web_intelligence_service(self.session),
        )
        trace: list[ReasoningStep] = []
        proposed_actions: list[ProposedAction] = []
        tool_calls = 0

        async def record(thought: str, action: str, observation: str, next_step: str) -> None:
            trace.append(
                ReasoningStep(
                    thought=thought,
                    action=action,
                    observation=observation,
                    next_step=next_step,
                )
            )

        if tool_calls < self.max_tool_calls:
            history = await tools.get_thread_history(email.sender)
            tool_calls += 1
            await record(
                "The agent needs full conversation context before deciding actions.",
                "get_thread_history",
                f"Found {len(history['emails'])} email(s) from this sender.",
                "Review policy context.",
            )

        rag_query = _rag_query_for_email(email)
        if tool_calls < self.max_tool_calls:
            rag_result = await tools.search_knowledge_base(rag_query)
            tool_calls += 1
            sources = sorted({item["source_doc"] for item in rag_result["results"]})
            await record(
                "The agent needs internal policy grounding before acting.",
                "search_knowledge_base",
                f"Retrieved policy sources: {', '.join(sources) if sources else 'none'}.",
                "Check customer/account context.",
            )
        else:
            sources = []

        if tool_calls < self.max_tool_calls:
            account = await tools.check_account_status(email.sender)
            tool_calls += 1
            await record(
                "The action depends on customer tier, value, and churn risk.",
                "check_account_status",
                f"Account status found: {account.get('found')}.",
                "Choose required action.",
            )

        web_trigger = should_trigger_web_intelligence(email)
        if web_trigger.triggered and tool_calls < self.max_tool_calls:
            company_name = (
                email.contact.company
                if getattr(email, "contact", None) is not None and email.contact.company
                else email.sender.split("@")[-1].split(".")[0]
            )
            if dry_run:
                observation = (
                    "Would fetch Market Intelligence because: "
                    + ", ".join(web_trigger.reasons)
                )
            else:
                market_intelligence = await tools.scrape_public_sentiment(company_name)
                observation = market_intelligence.get("market_intelligence_block", "")
            tool_calls += 1
            await record(
                "The email has reputation or public-sentiment risk triggers.",
                "scrape_public_sentiment",
                observation,
                "Use Market Intelligence in action planning.",
            )

        block_reason = auto_reply_block_reason(email)
        required_actions = _required_actions(email)

        if "legal" in required_actions and tool_calls < self.max_tool_calls:
            proposed_actions.append(
                ProposedAction(
                    action_type="Legal-Flag",
                    reason="Legal/compliance language requires legal review.",
                    would_execute=not dry_run,
                )
            )
            if not dry_run:
                await tools.flag_for_legal(
                    email=email,
                    issue_type="Legal or compliance escalation",
                    reasoning_log=[step.model_dump() for step in trace],
                )
            tool_calls += 1
            await record(
                "Mandatory legal/compliance rule applies.",
                "flag_for_legal",
                "Legal flag proposed." if dry_run else "Legal flag created.",
                "Create ticket or escalate.",
            )

        if "ticket" in required_actions and tool_calls < self.max_tool_calls:
            proposed_actions.append(
                ProposedAction(
                    action_type="Ticket-Created",
                    reason="A specialist team must own the follow-up.",
                    would_execute=not dry_run,
                )
            )
            if not dry_run:
                await tools.create_internal_ticket(
                    email=email,
                    title=f"Triage follow-up for email {email.id}",
                    body=email.classification_raw.get("escalation_reason", email.body)
                    if email.classification_raw
                    else email.body,
                    assignee=_assignee_for_email(email),
                    priority=email.urgency.value if email.urgency else "Medium",
                )
            tool_calls += 1
            await record(
                "The case requires a durable internal owner.",
                "create_internal_ticket",
                "Ticket proposed." if dry_run else "Ticket created.",
                "Escalate if required.",
            )

        if "draft" in required_actions and tool_calls < self.max_tool_calls:
            draft = await tools.draft_reply(
                context=email.body,
                tone="empathetic",
                policy_refs=sources,
            )
            tool_calls += 1
            proposed_actions.append(
                ProposedAction(
                    action_type="Auto-Reply",
                    reason="Draft reply prepared for review.",
                    would_execute=False,
                    safety_block_reason=block_reason,
                )
            )
            if not dry_run:
                await repository.create_action(
                    email_id=email.id,
                    action_type=ActionType.AUTO_REPLY,
                    reasoning_log=[step.model_dump() for step in trace],
                    proposed_content=draft["draft"],
                    status=ActionStatus.BLOCKED if block_reason else ActionStatus.PROPOSED,
                    safety_block_reason=block_reason,
                    tool_name="draft_reply",
                    tool_input={"tone": "empathetic", "policy_refs": sources},
                    tool_output=draft,
                )
            await record(
                "A reply can be drafted, but sending must respect the safety gate.",
                "draft_reply",
                draft["draft"],
                "Escalate for human review." if "escalate" in required_actions else "Wait for approval.",
            )

        if "escalate" in required_actions and tool_calls < self.max_tool_calls:
            reason = _escalation_reason(email)
            proposed_actions.append(
                ProposedAction(
                    action_type="Escalate",
                    reason=reason,
                    would_execute=not dry_run,
                )
            )
            if not dry_run:
                await tools.escalate_to_human(
                    email=email,
                    reason=reason,
                    priority=email.urgency.value if email.urgency else "Medium",
                    reasoning_log=[step.model_dump() for step in trace],
                )
            tool_calls += 1
            await record(
                "Human review is required before resolution.",
                "escalate_to_human",
                "Escalation proposed." if dry_run else "Escalation created.",
                "Stop or wait for human review.",
            )

        if tool_calls >= self.max_tool_calls and "escalate" not in required_actions:
            proposed_actions.append(
                ProposedAction(
                    action_type="Escalate",
                    reason="Agent reached maximum tool calls before resolution.",
                    would_execute=False if dry_run else True,
                )
            )

        if not dry_run:
            await self.session.commit()

        return AgentRunResponse(
            email_id=email.id,
            dry_run=dry_run,
            reasoning_trace=trace,
            proposed_actions=proposed_actions,
            tool_call_count=tool_calls,
            max_tool_calls=self.max_tool_calls,
            final_status="planned" if dry_run else "executed",
        )


def create_react_agent_service(session: AsyncSession) -> ReActAgentService:
    settings = get_settings()
    return ReActAgentService(session=session, max_tool_calls=settings.agent_max_tool_calls)


def _required_actions(email: Email) -> set[str]:
    actions: set[str] = set()
    scenario_codes = set((email.heuristic_flags or {}).get("scenario_codes", []))
    if "SECURITY_RANSOMWARE" in scenario_codes or "SECURITY_SUSPICIOUS_LOGIN" in scenario_codes:
        actions.update({"ticket", "escalate"})
        return actions
    if "GDPR_ARTICLE_20" in scenario_codes:
        actions.update({"legal", "ticket", "draft", "escalate"})
        return actions
    if "CHATBOT_MISINFORMATION" in scenario_codes:
        actions.update({"ticket", "draft", "escalate"})
        return actions
    if "NADIA_DATA_CORRUPTION_BUG" in scenario_codes:
        actions.update({"ticket", "escalate", "draft"})
        return actions
    if "KAREN_REPUTATION_CRISIS" in scenario_codes:
        actions.update({"ticket", "draft", "escalate"})
        return actions
    if "BOB_SLA_LEGAL_ESCALATION" in scenario_codes:
        actions.update({"legal", "draft", "escalate"})
        return actions
    if email.category == EmailCategory.LEGAL:
        actions.update({"legal", "draft", "escalate"})
    elif email.category == EmailCategory.COMPLIANCE:
        actions.update({"legal", "ticket", "escalate", "draft"})
    elif email.urgency == EmailUrgency.CRITICAL or email.requires_human:
        actions.update({"ticket", "escalate", "draft"})
    elif email.category in (EmailCategory.BUG_REPORT, EmailCategory.COMPLAINT):
        actions.update({"ticket", "escalate", "draft"})
    else:
        actions.add("draft")
    return actions


def _rag_query_for_email(email: Email) -> str:
    return f"{email.subject or ''} {email.body} {email.category.value if email.category else ''}"


def _assignee_for_email(email: Email) -> str:
    if email.category == EmailCategory.COMPLIANCE:
        return "compliance"
    if email.category == EmailCategory.LEGAL:
        return "legal"
    if email.category == EmailCategory.BUG_REPORT:
        return "engineering"
    return "support-leadership"


def _escalation_reason(email: Email) -> str:
    if email.classification_raw and email.classification_raw.get("escalation_reason"):
        return str(email.classification_raw["escalation_reason"])
    if email.urgency == EmailUrgency.CRITICAL:
        return "Critical urgency requires human review."
    if email.requires_human:
        return "Classifier or business rules require human review."
    return "Agent escalation required."
