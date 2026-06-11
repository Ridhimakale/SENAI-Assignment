import pytest

from app.models.enums import EmailCategory, EmailUrgency
from app.services.intelligence.classifier_provider import GroqClassifierProvider


class _FakeMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeChoice:
    def __init__(self, content: str) -> None:
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content: str) -> None:
        self.choices = [_FakeChoice(content)]


class _FakeCompletions:
    async def create(self, **kwargs):
        return _FakeResponse(
            """
            {
              "category": "Billing",
              "sentiment": "Mixed",
              "sentiment_score": -0.25,
              "urgency": "High",
              "requires_human": true,
              "escalation_reason": "Conflicting billing signals need review.",
              "suggested_reply": null,
              "confidence": 0.88,
              "detected_entities": {
                "order_ids": [],
                "ticket_ids": [],
                "monetary_amounts": ["$49"],
                "deadlines": [],
                "products_mentioned": ["pro plan"]
              }
            }
            """
        )


class _FakeChat:
    def __init__(self) -> None:
        self.completions = _FakeCompletions()


class _FakeClient:
    def __init__(self) -> None:
        self.chat = _FakeChat()


@pytest.mark.asyncio
async def test_groq_classifier_parses_json_response() -> None:
    provider = GroqClassifierProvider(
        api_key="test-key",
        model_name="llama-3.1-70b-versatile",
        client=_FakeClient(),
    )

    output = await provider.classify(
        prompt="test prompt",
        email_text="I love the product but hate the pricing and want a refund.",
    )

    assert output["category"] == EmailCategory.BILLING.value
    assert output["urgency"] == EmailUrgency.HIGH.value
    assert output["requires_human"] is True
    assert output["confidence"] == 0.88
