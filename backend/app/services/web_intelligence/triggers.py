from app.models.email import Email
from app.models.enums import EmailCategory, EmailUrgency
from app.schemas.web_intelligence import WebIntelligenceTriggerResult


TRIGGER_TERMS = (
    "public review",
    "negative review",
    "bad review",
    "trustpilot",
    "g2",
    "twitter",
    "x.com",
    "post publicly",
    "social media",
    "press",
    "investor",
)


def should_trigger_web_intelligence(email: Email) -> WebIntelligenceTriggerResult:
    reasons: list[str] = []
    text = f"{email.subject or ''} {email.body or ''}".lower()

    matched_terms = [term for term in TRIGGER_TERMS if term in text]
    if matched_terms:
        reasons.append(f"public_signal_terms:{','.join(matched_terms)}")

    if email.sentiment_score is not None and email.sentiment_score < -0.6:
        reasons.append("sentiment_below_-0.6")

    if email.category == EmailCategory.COMPLAINT and email.urgency in (
        EmailUrgency.HIGH,
        EmailUrgency.CRITICAL,
    ):
        reasons.append("high_urgency_complaint")

    if "press" in text or "investor" in text:
        reasons.append("press_or_investor_inquiry")

    scenario_codes = set((email.heuristic_flags or {}).get("scenario_codes", []))
    if "KAREN_REPUTATION_CRISIS" in scenario_codes:
        reasons.append("karen_reputation_crisis")

    return WebIntelligenceTriggerResult(triggered=bool(reasons), reasons=reasons)
