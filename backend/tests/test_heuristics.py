from app.models.enums import ActionType, EmailCategory, EmailStatus, EmailUrgency
from app.services.intelligence.heuristics import evaluate_email_heuristics


def test_spam_email_is_ignored_and_stops_processing() -> None:
    result = evaluate_email_heuristics(
        sender="pitch@seo-growth.biz",
        subject="SEO services",
        body="We can help you rank #1 with backlinks.",
    )

    assert result.category == EmailCategory.SPAM
    assert result.status == EmailStatus.IGNORED
    assert result.action_type == ActionType.IGNORED
    assert result.stop_processing is True


def test_internal_email_is_routed_away_from_customer_workflow() -> None:
    result = evaluate_email_heuristics(
        sender="ops@internal.com",
        subject="Internal handoff",
        body="Please assign this to support.",
    )

    assert result.category == EmailCategory.INTERNAL
    assert result.status == EmailStatus.IGNORED
    assert result.flags["is_internal"] is True
    assert result.stop_processing is True


def test_ransomware_is_critical_security_and_blocks_processing() -> None:
    result = evaluate_email_heuristics(
        sender="attacker@example.net",
        subject="Ransomware notice",
        body="Send 2 BTC or we publish your data.",
    )

    assert result.urgency == EmailUrgency.CRITICAL
    assert result.status == EmailStatus.ESCALATED
    assert result.requires_human is True
    assert result.flags["is_critical_security"] is True
    assert result.action_type == ActionType.ESCALATE
    assert result.stop_processing is True


def test_legal_urgent_email_requires_human_but_continues_to_next_stage() -> None:
    result = evaluate_email_heuristics(
        sender="bob.jones@enterprise.net",
        subject="Legal escalation: SLA breach",
        body="Our legal team is reviewing this P0 incident.",
    )

    assert result.category == EmailCategory.LEGAL
    assert result.urgency == EmailUrgency.CRITICAL
    assert result.status == EmailStatus.PROCESSING
    assert result.requires_human is True
    assert result.stop_processing is False


def test_normal_customer_email_gets_low_urgency_processing_status() -> None:
    result = evaluate_email_heuristics(
        sender="alice@example.com",
        subject="Question about billing",
        body="Can you explain my invoice?",
    )

    assert result.category is None
    assert result.urgency == EmailUrgency.LOW
    assert result.status == EmailStatus.PROCESSING
    assert result.requires_human is False
    assert result.stop_processing is False
