from datetime import UTC, datetime

import app.db.base  # noqa: F401
from app.models.email import Email
from app.models.enums import EmailCategory, EmailUrgency
from app.models.thread import Thread
from app.services.agents.react_service import _required_actions
from app.services.intelligence.scenarios import (
    ScenarioCode,
    evaluate_special_scenarios,
    merge_scenario_flags,
)


def make_email(
    *,
    sender: str,
    thread_id: str,
    subject: str,
    body: str,
    category: EmailCategory | None = None,
    urgency: EmailUrgency | None = None,
    sentiment_score: float | None = None,
) -> Email:
    email = Email(
        id=1,
        thread_id=1,
        contact_id=1,
        message_id="msg_test",
        sender=sender,
        subject=subject,
        body=body,
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        category=category,
        urgency=urgency,
        sentiment_score=sentiment_score,
    )
    email.thread = Thread(
        id=1,
        thread_id=thread_id,
        contact_id=1,
        sender_email=sender,
        first_seen_at=datetime(2026, 1, 1, tzinfo=UTC),
        last_updated_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    return email


def scenario_codes(email: Email, history: list[Email] | None = None) -> set[str]:
    evaluation = evaluate_special_scenarios(email=email, thread_history=history)
    return {scenario.code.value for scenario in evaluation.scenarios}


def test_gdpr_article_20_scenario_detected() -> None:
    email = make_email(
        sender="marcus.del@fintech-startup.co",
        thread_id="thread_gdpr_001",
        subject="GDPR Article 20 Request",
        body="This is a formal GDPR Article 20 data portability request.",
    )

    assert ScenarioCode.GDPR_ARTICLE_20.value in scenario_codes(email)


def test_ransomware_scenario_detected() -> None:
    email = make_email(
        sender="attacker@example.net",
        thread_id="thread_security_ransomware",
        subject="Ransomware",
        body="Send 2 BTC or we publish your data.",
    )

    assert ScenarioCode.SECURITY_RANSOMWARE.value in scenario_codes(email)


def test_karen_reputation_crisis_detects_public_review_threat() -> None:
    history = [
        make_email(
            sender="karen.w@retail-co.com",
            thread_id="thread_karen_refund",
            subject="Refund complaint",
            body="I want a refund.",
            sentiment_score=-0.5,
        ),
        make_email(
            sender="karen.w@retail-co.com",
            thread_id="thread_karen_refund",
            subject="Still no reply",
            body="This is terrible and I will cancel.",
            sentiment_score=-0.7,
        ),
        make_email(
            sender="karen.w@retail-co.com",
            thread_id="thread_karen_refund",
            subject="Public review",
            body="I will post publicly on Trustpilot and G2.",
            sentiment_score=-0.9,
        ),
    ]

    assert ScenarioCode.KAREN_REPUTATION_CRISIS.value in scenario_codes(history[-1], history)


def test_alice_pricing_context_detected() -> None:
    email = make_email(
        sender="alice.smith@greenlight-npo.org",
        thread_id="thread_alice_pricing",
        subject="Pro-rata billing question",
        body="How does the nonprofit discount affect upgrade billing?",
    )

    assert ScenarioCode.ALICE_PRICING_CONTEXT.value in scenario_codes(email)


def test_bob_sla_legal_scenario_detected() -> None:
    email = make_email(
        sender="bob.jones@enterprise.net",
        thread_id="thread_bob_outage",
        subject="Escalation: SLA Breach + Legal Review",
        body="Our legal team is reviewing the RCA and SLA credit obligations.",
    )

    assert ScenarioCode.BOB_SLA_LEGAL_ESCALATION.value in scenario_codes(email)


def test_chatbot_misinformation_detected() -> None:
    email = make_email(
        sender="customer@example.com",
        thread_id="thread_chatbot_misinformation",
        subject="Wrong refund info",
        body="Your chatbot gave wrong refund information and this is misinformation.",
    )

    assert ScenarioCode.CHATBOT_MISINFORMATION.value in scenario_codes(email)


def test_nadia_data_corruption_detected() -> None:
    email = make_email(
        sender="nadia@example.com",
        thread_id="thread_nadia_bug",
        subject="Silent data corruption",
        body="The success message appears but data is missing.",
    )

    assert ScenarioCode.NADIA_DATA_CORRUPTION_BUG.value in scenario_codes(email)


def test_bigcorp_rfp_detected() -> None:
    email = make_email(
        sender="procurement@bigcorp.com",
        thread_id="thread_bigcorp_rfp",
        subject="RFP and compliance audit",
        body="This is linked to a $2.4M opportunity.",
    )

    assert ScenarioCode.BIGCORP_RFP_OPPORTUNITY.value in scenario_codes(email)


def test_eleanor_hipaa_enterprise_detected() -> None:
    email = make_email(
        sender="eleanor@health-enterprise.com",
        thread_id="thread_eleanor_compliance",
        subject="HIPAA BAA for 200 seats",
        body="We need HIPAA compliance and a BAA before our deadline.",
    )

    assert ScenarioCode.ELEANOR_HIPAA_ENTERPRISE.value in scenario_codes(email)


def test_scenario_flags_drive_agent_required_actions() -> None:
    email = make_email(
        sender="marcus.del@fintech-startup.co",
        thread_id="thread_gdpr_001",
        subject="GDPR Article 20 Request",
        body="Formal Article 20 data portability request.",
        category=EmailCategory.COMPLIANCE,
        urgency=EmailUrgency.HIGH,
    )
    evaluation = evaluate_special_scenarios(email=email, thread_history=[email])
    email.heuristic_flags = merge_scenario_flags({}, evaluation)

    assert _required_actions(email) == {"legal", "ticket", "draft", "escalate"}
