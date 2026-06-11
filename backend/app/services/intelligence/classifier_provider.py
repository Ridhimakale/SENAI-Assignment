from __future__ import annotations

import json
from typing import Any, Protocol

from app.models.enums import EmailCategory, EmailUrgency
from app.schemas.classification import ClassificationOutput
from app.services.intelligence.entity_extraction import extract_entities

GROQ_OPENAI_BASE_URL = "https://api.groq.com/openai/v1"


class ClassifierProvider(Protocol):
    model_name: str

    async def classify(self, prompt: str, email_text: str) -> dict:
        pass


class OpenAIClassifierProvider:
    def __init__(self, *, api_key: str, model_name: str, client: Any | None = None) -> None:
        from openai import AsyncOpenAI

        self.client = client or AsyncOpenAI(api_key=api_key)
        self.model_name = model_name

    async def classify(self, prompt: str, email_text: str) -> dict:
        return await _classify_with_client(self.client, self.model_name, prompt)


class GroqClassifierProvider:
    def __init__(self, *, api_key: str, model_name: str, client: Any | None = None) -> None:
        from openai import AsyncOpenAI

        self.client = client or AsyncOpenAI(
            api_key=api_key,
            base_url=GROQ_OPENAI_BASE_URL,
        )
        self.model_name = model_name

    async def classify(self, prompt: str, email_text: str) -> dict:
        return await _classify_with_client(self.client, self.model_name, prompt)


class RuleBasedClassifierProvider:
    model_name = "rule_based_fallback"

    async def classify(self, prompt: str, email_text: str) -> dict:
        text = email_text.lower()
        category = EmailCategory.OTHER
        urgency = EmailUrgency.LOW
        sentiment = "Neutral"
        sentiment_score = 0.0
        requires_human = False
        escalation_reason = None
        suggested_reply = "Thanks for reaching out. We are reviewing your request."
        confidence = 0.76

        if any(word in text for word in ("refund", "charge", "invoice", "billing", "pro-rata")):
            category = EmailCategory.BILLING
        if any(word in text for word in ("bug", "missing data", "corruption", "not working")):
            category = EmailCategory.BUG_REPORT
            urgency = EmailUrgency.HIGH
            requires_human = True
            escalation_reason = "Potential product defect or data issue requires human review."
            suggested_reply = None
        if any(word in text for word in ("gdpr", "article 20", "data portability", "dpa", "hipaa")):
            category = EmailCategory.COMPLIANCE
            urgency = EmailUrgency.HIGH
            requires_human = True
            escalation_reason = "Compliance request requires human review and ticket creation."
            suggested_reply = None
        if any(word in text for word in ("legal", "cease and desist", "lawsuit", "attorney")):
            category = EmailCategory.LEGAL
            urgency = EmailUrgency.CRITICAL
            requires_human = True
            escalation_reason = "Legal language requires mandatory escalation."
            suggested_reply = None
        if any(word in text for word in ("urgent", "p0", "ransomware", "breach")):
            urgency = EmailUrgency.CRITICAL
            requires_human = True
            escalation_reason = escalation_reason or "Critical urgency detected."
            suggested_reply = None
        if any(word in text for word in ("angry", "hate", "terrible", "cancel", "churn", "review")):
            sentiment = "Negative"
            sentiment_score = -0.75
        if any(word in text for word in ("love", "great", "thanks")) and sentiment == "Negative":
            sentiment = "Mixed"
            sentiment_score = -0.25
            confidence = 0.68
        elif any(word in text for word in ("love", "great", "thanks")):
            sentiment = "Positive"
            sentiment_score = 0.65

        entities = extract_entities(email_text)
        output = ClassificationOutput(
            category=category,
            sentiment=sentiment,
            sentiment_score=sentiment_score,
            urgency=urgency,
            requires_human=requires_human,
            escalation_reason=escalation_reason,
            suggested_reply=suggested_reply,
            confidence=confidence,
            detected_entities=entities,
        )
        return output.model_dump(mode="json")


async def _classify_with_client(client: Any, model_name: str, prompt: str) -> dict:
    response = await client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": "Return only valid JSON matching the schema."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content or "{}"
    return _safe_json_loads(content)


def _safe_json_loads(content: str) -> dict:
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise
