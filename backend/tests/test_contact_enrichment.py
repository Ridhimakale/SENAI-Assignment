from datetime import UTC, datetime
from decimal import Decimal

import app.db.base
from app.models.contact import Contact
from app.models.email import Email
from app.models.enums import EmailUrgency
from app.services.intelligence.contact_enrichment import enrich_contact_profile
from app.services.intelligence.scenarios import ScenarioCode, ScenarioDirective, ScenarioEvaluation


def test_enrichment_marks_enterprise_bob_as_vip() -> None:
    contact = Contact(id=1, email="bob.jones@enterprise.net", company="Enterprise")
    emails = [
        Email(
            id=1,
            thread_id=1,
            contact_id=1,
            message_id="msg_001",
            sender="bob.jones@enterprise.net",
            subject="P0 incident",
            body="We need SLA credits for our 200 seats and legal review.",
            timestamp=datetime(2023, 10, 1, tzinfo=UTC),
        )
    ]
    evaluation = ScenarioEvaluation(
        scenarios=[
            ScenarioDirective(
                code=ScenarioCode.BOB_SLA_LEGAL_ESCALATION,
                severity=EmailUrgency.CRITICAL,
                requires_human=True,
                recommended_actions=["flag_for_legal"],
                notes="Bob escalation chain",
            )
        ]
    )

    result = enrich_contact_profile(
        contact=contact,
        emails=emails,
        scenario_evaluation=evaluation,
    )

    assert result.status.value == "VIP"
    assert result.subscription_tier == "Enterprise"
    assert result.renewal_status == "At Risk"
    assert result.account_value is not None
    assert result.account_value >= Decimal("10000")
    assert "High Revenue" in (result.vip_reason or "")


def test_enrichment_increases_karen_churn_risk() -> None:
    contact = Contact(id=2, email="karen.w@retail-co.com", company="Retail Co")
    emails = [
        Email(
            id=1,
            thread_id=1,
            contact_id=2,
            message_id="msg_001",
            sender="karen.w@retail-co.com",
            subject="Refund request",
            body="I am angry and may post publicly on Trustpilot.",
            sentiment_score=-0.8,
            timestamp=datetime(2023, 10, 1, tzinfo=UTC),
        ),
        Email(
            id=2,
            thread_id=1,
            contact_id=2,
            message_id="msg_002",
            sender="karen.w@retail-co.com",
            subject="Follow up",
            body="This is a complaint and I want a refund.",
            sentiment_score=-0.7,
            timestamp=datetime(2023, 10, 2, tzinfo=UTC),
        ),
        Email(
            id=3,
            thread_id=1,
            contact_id=2,
            message_id="msg_003",
            sender="karen.w@retail-co.com",
            subject="Third follow up",
            body="Still unhappy and considering a public review.",
            sentiment_score=-0.9,
            timestamp=datetime(2023, 10, 3, tzinfo=UTC),
        ),
    ]
    evaluation = ScenarioEvaluation(
        scenarios=[
            ScenarioDirective(
                code=ScenarioCode.KAREN_REPUTATION_CRISIS,
                severity=EmailUrgency.HIGH,
                requires_human=True,
                recommended_actions=["create_retention_case"],
                notes="Karen retention threat",
            )
        ]
    )

    result = enrich_contact_profile(
        contact=contact,
        emails=emails,
        scenario_evaluation=evaluation,
    )

    assert result.status.value == "VIP" or result.status.value == "Active"
    assert result.churn_risk_score >= 0.7
    assert result.renewal_status == "At Risk"
    assert "public_reputation_threat" in result.metadata_json["risk_factors"]
