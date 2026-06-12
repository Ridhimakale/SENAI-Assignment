from dataclasses import dataclass


@dataclass(frozen=True)
class LangChainAgentConfig:
    groq_api_key: str
    groq_model: str
    max_iterations: int


def build_react_system_instructions() -> str:
    return """
You are a single ReAct triage agent for a CRM intelligence platform.

Goal:
Choose the safest and most appropriate actions using tools, thread history, account context, RAG, and optional market intelligence.

Reasoning loop:
Thought -> Action -> Observation -> Next Step

Rules:
- Maximum 6 tool calls.
- The classifier owns understanding; the agent owns actions.
- Never auto-reply to spam, ransomware, legal threats, or Critical urgency emails.
- GDPR, legal, and security cases require mandatory escalation.
- Prefer internal knowledge before drafting policy-sensitive replies.
- If the case remains unresolved after the allowed tools, escalate to a human.
- Keep the reasoning trace concise, structured, and easy to audit.
""".strip()


def create_langchain_groq_llm(config: LangChainAgentConfig):
    try:
        from langchain_groq import ChatGroq
    except Exception as exc:
        raise RuntimeError(
            "LangChain Groq integration is unavailable. Install langchain-groq."
        ) from exc

    return ChatGroq(
        api_key=config.groq_api_key,
        model=config.groq_model,
        temperature=0,
        max_retries=2,
    )


def langchain_agent_available() -> bool:
    try:
        import langchain  # noqa: F401
        import langchain_groq  # noqa: F401
    except Exception:
        return False
    return True
