import pytest

from app.models.enums import EmailCategory, EmailUrgency
from app.schemas.classification import ClassificationOutput
from app.services.intelligence.classifier_provider import RuleBasedClassifierProvider


def test_classification_schema_rejects_invalid_category() -> None:
    try:
        ClassificationOutput.model_validate(
            {
                "category": "banana",
                "sentiment": "Neutral",
                "sentiment_score": 0,
                "urgency": "Low",
                "requires_human": False,
                "escalation_reason": None,
                "suggested_reply": "Thanks.",
                "confidence": 0.9,
                "detected_entities": {},
            }
        )
    except Exception as exc:
        assert "category" in str(exc)
    else:
        raise AssertionError("Invalid category should fail validation.")


def test_classification_schema_requires_escalation_reason_for_human_review() -> None:
    try:
        ClassificationOutput.model_validate(
            {
                "category": "Legal",
                "sentiment": "Negative",
                "sentiment_score": -0.7,
                "urgency": "Critical",
                "requires_human": True,
                "escalation_reason": None,
                "suggested_reply": None,
                "confidence": 0.95,
                "detected_entities": {},
            }
        )
    except Exception as exc:
        assert "escalation_reason" in str(exc)
    else:
        raise AssertionError("Human-review classifications need a reason.")


@pytest.mark.asyncio
async def test_rule_based_classifier_handles_conflicting_signal_with_low_confidence() -> None:
    provider = RuleBasedClassifierProvider()

    output = await provider.classify(
        prompt="",
        email_text="I love the product but hate the pricing and want a refund.",
    )

    assert output["category"] == EmailCategory.BILLING.value
    assert output["sentiment"] == "Mixed"
    assert output["confidence"] < 0.70


@pytest.mark.asyncio
async def test_rule_based_classifier_detects_gdpr_article_20() -> None:
    provider = RuleBasedClassifierProvider()

    output = await provider.classify(
        prompt="",
        email_text="This is a formal GDPR Article 20 data portability request.",
    )

    assert output["category"] == EmailCategory.COMPLIANCE.value
    assert output["urgency"] == EmailUrgency.HIGH.value
    assert output["requires_human"] is True
