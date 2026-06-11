from dataclasses import dataclass


@dataclass(frozen=True)
class LangChainAgentConfig:
    groq_api_key: str
    groq_model: str
    max_iterations: int


def build_react_system_instructions() -> str:
    return """
You are a single ReAct triage agent for a CRM intelligence platform.

You must reason using this loop:
Thought -> Action -> Observation -> Next Step

Rules:
- Maximum 6 tool calls.
- Classifier owns understanding; agent owns actions.
- Never auto-reply to spam, ransomware, legal threats, or Critical urgency emails.
- GDPR, legal, and security cases require mandatory escalation.
- Use internal knowledge before drafting policy-sensitive replies.
- Return a structured action plan that can be stored as an audit trace.
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
