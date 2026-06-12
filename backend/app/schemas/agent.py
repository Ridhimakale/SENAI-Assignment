from pydantic import BaseModel, Field


class ReasoningStep(BaseModel):
    thought: str
    action: str
    observation: str
    next_step: str


class ProposedAction(BaseModel):
    action_type: str
    reason: str
    would_execute: bool
    safety_block_reason: str | None = None


class AgentRunResponse(BaseModel):
    email_id: int
    dry_run: bool
    reasoning_trace: list[ReasoningStep]
    proposed_actions: list[ProposedAction]
    draft_preview: str | None = None
    tool_call_count: int
    max_tool_calls: int
    final_status: str


class DraftGenerationResponse(BaseModel):
    email_id: int
    draft: str
    policy_refs: list[str]
    model_name: str | None = None
    provider: str | None = None
