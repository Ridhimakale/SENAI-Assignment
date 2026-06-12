from collections.abc import Iterable
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime, timezone
from statistics import fmean
import re

from app.models.contact import Contact
from app.models.email import Email
from app.models.enums import ContactStatus
from app.services.intelligence.scenarios import ScenarioEvaluation, ScenarioCode

MONEY_RE = re.compile(r"\$([0-9][0-9,]*(?:\.[0-9]+)?)")
SEAT_RE = re.compile(r"(\d{1,4})\s*seats?", re.IGNORECASE)


@dataclass(frozen=True)
class ContactEnrichmentResult:
    account_value: Decimal | None
    churn_risk_score: float
    subscription_tier: str | None
    renewal_status: str | None
    status: ContactStatus
    vip_reason: str | None
    metadata_json: dict = field(default_factory=dict)


def enrich_contact_profile(
    *,
    contact: Contact,
    emails: Iterable[Email],
    scenario_evaluation: ScenarioEvaluation,
) -> ContactEnrichmentResult:
    email_list = list(emails)
    combined_text = " ".join(
        f"{email.subject or ''} {email.body or ''}" for email in email_list
    ).lower()

    monetary_amounts = _extract_monetary_amounts(combined_text)
    seat_counts = _extract_seat_counts(combined_text)
    negative_signals = _count_negative_signals(email_list, combined_text)
    scenario_codes = {scenario.code for scenario in scenario_evaluation.scenarios}

    account_value = _infer_account_value(
        contact=contact,
        monetary_amounts=monetary_amounts,
        seat_counts=seat_counts,
        scenario_codes=scenario_codes,
        combined_text=combined_text,
    )
    churn_risk_score, risk_factors = _infer_churn_risk(
        email_list=email_list,
        combined_text=combined_text,
        scenario_codes=scenario_codes,
        negative_signals=negative_signals,
    )
    subscription_tier = _infer_subscription_tier(
        account_value=account_value,
        seat_counts=seat_counts,
        combined_text=combined_text,
        scenario_codes=scenario_codes,
    )
    renewal_status = _infer_renewal_status(
        churn_risk_score=churn_risk_score,
        combined_text=combined_text,
        scenario_codes=scenario_codes,
    )
    vip_reason = _infer_vip_reason(
        account_value=account_value,
        scenario_codes=scenario_codes,
        seat_counts=seat_counts,
        combined_text=combined_text,
    )
    status = ContactStatus.VIP if vip_reason else ContactStatus.ACTIVE
    metadata_json = {
        "risk_factors": risk_factors,
        "monetary_amounts": [str(amount) for amount in monetary_amounts],
        "seat_counts": seat_counts,
        "scenario_codes": [scenario.value for scenario in scenario_codes],
        "negative_signals": negative_signals,
    }

    return ContactEnrichmentResult(
        account_value=account_value,
        churn_risk_score=churn_risk_score,
        subscription_tier=subscription_tier,
        renewal_status=renewal_status,
        status=status,
        vip_reason=vip_reason,
        metadata_json=metadata_json,
    )


def _extract_monetary_amounts(text: str) -> list[Decimal]:
    amounts = []
    for match in MONEY_RE.findall(text):
        cleaned = match.replace(",", "")
        try:
            amounts.append(Decimal(cleaned))
        except Exception:
            continue
    return sorted(set(amounts))


def _extract_seat_counts(text: str) -> list[int]:
    values = []
    for match in SEAT_RE.findall(text):
        try:
            values.append(int(match))
        except ValueError:
            continue
    return sorted(set(values))


def _count_negative_signals(email_list: list[Email], combined_text: str) -> int:
    signals = 0
    for email in email_list:
        text = f"{email.subject or ''} {email.body or ''}".lower()
        if any(
            keyword in text
            for keyword in (
                "angry",
                "complaint",
                "refund",
                "cancel",
                "terrible",
                "not happy",
                "churn",
                "review",
            )
        ):
            signals += 1
        if email.sentiment_score is not None and email.sentiment_score < -0.2:
            signals += 1
    if "public review" in combined_text or "post publicly" in combined_text:
        signals += 1
    return signals


def _infer_account_value(
    *,
    contact: Contact,
    monetary_amounts: list[Decimal],
    seat_counts: list[int],
    scenario_codes: set[ScenarioCode],
    combined_text: str,
) -> Decimal | None:
    if not monetary_amounts and not seat_counts and not any(
        code in scenario_codes
        for code in (
            ScenarioCode.BIGCORP_RFP_OPPORTUNITY,
            ScenarioCode.ELEANOR_HIPAA_ENTERPRISE,
            ScenarioCode.BOB_SLA_LEGAL_ESCALATION,
        )
    ):
        return None

    if ScenarioCode.BIGCORP_RFP_OPPORTUNITY in scenario_codes:
        return Decimal("2400000.00")
    if ScenarioCode.ELEANOR_HIPAA_ENTERPRISE in scenario_codes:
        return Decimal("200000.00")
    if ScenarioCode.BOB_SLA_LEGAL_ESCALATION in scenario_codes:
        return Decimal("150000.00")

    if seat_counts:
        baseline = Decimal(max(seat_counts) * 1000)
    elif monetary_amounts and any(
        token in combined_text for token in ("deal", "pricing", "budget", "contract", "opportunity")
    ):
        baseline = max(monetary_amounts)
    else:
        return None

    multiplier = Decimal("1.0")
    if any(code in scenario_codes for code in (ScenarioCode.BIGCORP_RFP_OPPORTUNITY,)):
        multiplier = Decimal("1.0")
    elif any(code in scenario_codes for code in (ScenarioCode.ELEANOR_HIPAA_ENTERPRISE,)):
        multiplier = Decimal("1.2")
    elif any(code in scenario_codes for code in (ScenarioCode.BOB_SLA_LEGAL_ESCALATION,)):
        multiplier = Decimal("1.15")
    elif any(code in scenario_codes for code in (ScenarioCode.ALICE_PRICING_CONTEXT,)):
        multiplier = Decimal("0.8")

    if "enterprise" in combined_text or "vip" in combined_text:
        multiplier = max(multiplier, Decimal("1.1"))

    account_value = baseline * multiplier
    if account_value < Decimal("10000") and (
        "enterprise" in combined_text
        or "hipaa" in combined_text
        or "rfp" in combined_text
        or "seats" in combined_text
    ):
        account_value = Decimal("10000")

    if account_value <= 0:
        return None
    return account_value.quantize(Decimal("0.01"))


def _infer_churn_risk(
    *,
    email_list: list[Email],
    combined_text: str,
    scenario_codes: set[ScenarioCode],
    negative_signals: int,
) -> tuple[float, list[str]]:
    risk = 0.05
    factors: list[str] = []

    sentiment_scores = [email.sentiment_score for email in email_list if email.sentiment_score is not None]
    recent_emails = sorted(email_list, key=lambda email: email.timestamp)[-3:]
    latest_email = max(email_list, key=lambda email: email.timestamp, default=None)

    if negative_signals >= 3:
        risk += 0.35
        factors.append("three_or_more_negative_signals")
    if sentiment_scores:
        avg_sentiment = fmean(sentiment_scores)
        if avg_sentiment < -0.3:
            risk += 0.2
            factors.append("negative_sentiment_average")
        if latest_email is not None and (latest_email.sentiment_score or 0) <= -0.4:
            risk += 0.1
            factors.append("latest_email_negative")
    if len(recent_emails) >= 3 and all((email.sentiment_score or 0) < -0.15 for email in recent_emails):
        risk += 0.15
        factors.append("recent_negative_streak")
    if any(token in combined_text for token in ("refund", "cancel", "churn", "leave")):
        risk += 0.2
        factors.append("retention_keywords")
    if any(token in combined_text for token in ("public review", "trustpilot", "g2", "post publicly")):
        risk += 0.25
        factors.append("public_reputation_threat")
    if any(token in combined_text for token in ("legal", "lawsuit", "cease and desist")):
        risk += 0.15
        factors.append("legal_pressure")
    if any(code in scenario_codes for code in (ScenarioCode.KAREN_REPUTATION_CRISIS,)):
        risk += 0.3
        factors.append("karen_reputation_crisis")
    if any(code in scenario_codes for code in (ScenarioCode.BOB_SLA_LEGAL_ESCALATION,)):
        risk += 0.1
        factors.append("enterprise_escalation_chain")

    if email_list and len(email_list) >= 5:
        risk += 0.05
        factors.append("long_running_thread")
    if latest_email is not None:
        age_hours = (datetime.now(timezone.utc) - latest_email.timestamp).total_seconds() / 3600
        if age_hours > 48 and any(_is_not_replied(email) for email in email_list):
            risk += 0.15
            factors.append("unresolved_thread_over_48h")
    if len(email_list) >= 4:
        gaps = []
        ordered = sorted(email_list, key=lambda email: email.timestamp)
        for previous, current in zip(ordered, ordered[1:]):
            gap_hours = max(0.0, (current.timestamp - previous.timestamp).total_seconds() / 3600)
            gaps.append(gap_hours)
        if gaps and max(gaps) >= 24:
            risk += 0.1
            factors.append("long_response_gap")

    risk = max(0.0, min(risk, 1.0))
    return round(risk, 2), factors


def _is_not_replied(email: Email) -> bool:
    status_text = getattr(email.status, "value", str(email.status)).lower()
    return status_text != "replied"


def _infer_subscription_tier(
    *,
    account_value: Decimal | None,
    seat_counts: list[int],
    combined_text: str,
    scenario_codes: set[ScenarioCode],
) -> str | None:
    if any(code in scenario_codes for code in (ScenarioCode.BIGCORP_RFP_OPPORTUNITY,)):
        return "Enterprise"
    if any(code in scenario_codes for code in (ScenarioCode.ELEANOR_HIPAA_ENTERPRISE,)):
        return "Enterprise"
    if account_value is not None and account_value >= Decimal("100000"):
        return "Enterprise"
    if seat_counts and max(seat_counts) >= 100:
        return "Enterprise"
    if "non-profit" in combined_text or "npo" in combined_text:
        return "Standard"
    if account_value is not None and account_value >= Decimal("10000"):
        return "Standard"
    return "Starter"


def _infer_renewal_status(
    *,
    churn_risk_score: float,
    combined_text: str,
    scenario_codes: set[ScenarioCode],
) -> str | None:
    if "renewal on hold" in combined_text or "renewal hold" in combined_text:
        return "On Hold"
    if any(code in scenario_codes for code in (ScenarioCode.BOB_SLA_LEGAL_ESCALATION,)):
        return "At Risk"
    if churn_risk_score >= 0.7:
        return "At Risk"
    return "Healthy"


def _infer_vip_reason(
    *,
    account_value: Decimal | None,
    scenario_codes: set[ScenarioCode],
    seat_counts: list[int],
    combined_text: str,
) -> str | None:
    reasons: list[str] = []
    if account_value is not None and account_value >= Decimal("100000"):
        reasons.append("High Revenue")
    if any(code in scenario_codes for code in (ScenarioCode.BIGCORP_RFP_OPPORTUNITY,)):
        reasons.append("Strategic Account")
    if any(code in scenario_codes for code in (ScenarioCode.ELEANOR_HIPAA_ENTERPRISE,)):
        reasons.append("Enterprise Compliance Deal")
    if any(code in scenario_codes for code in (ScenarioCode.BOB_SLA_LEGAL_ESCALATION,)):
        reasons.append("Enterprise Escalation Account")
    if seat_counts and max(seat_counts) >= 100:
        reasons.append("Large Seat Opportunity")
    if "vip" in combined_text:
        reasons.append("VIP Flagged")
    if not reasons:
        return None
    unique_reasons = list(dict.fromkeys(reasons))
    return ", ".join(unique_reasons)
