from dataclasses import dataclass, field

from app.models.enums import ActionType, EmailCategory, EmailStatus, EmailUrgency
from app.services.ingestion.normalization import normalize_text

SPAM_KEYWORDS = (
    "seo services",
    "rank #1",
    "nigerian prince",
    "inheritance",
    "cold outreach",
    "guest post",
    "backlinks",
)
SPAM_DOMAINS = ("spam-mail.net", "seo-growth.biz", "coldoutreach.io")
INTERNAL_DOMAINS = ("internal.com", "mycompany.com")
SECURITY_KEYWORDS = (
    "ransomware",
    "send 2 btc",
    "publish your data",
    "credential compromise",
    "suspicious login",
    "data breach",
)
CRITICAL_SECURITY_KEYWORDS = (
    "ransomware",
    "send 2 btc",
    "publish your data",
    "data breach",
)
URGENCY_KEYWORDS = (
    "urgent",
    "p0",
    "legal",
    "cease and desist",
    "ransomware",
    "sla breach",
)
LEGAL_KEYWORDS = ("legal", "cease and desist", "lawsuit", "attorney", "gdpr")


@dataclass(frozen=True)
class HeuristicResult:
    category: EmailCategory | None
    urgency: EmailUrgency
    status: EmailStatus
    requires_human: bool
    flags: dict = field(default_factory=dict)
    action_type: ActionType | None = None
    action_reason: str | None = None
    stop_processing: bool = False


def evaluate_email_heuristics(
    *, sender: str, subject: str | None, body: str | None
) -> HeuristicResult:
    text = f"{normalize_text(subject)} {normalize_text(body)}".lower()
    domain = _sender_domain(sender)

    spam_matches = _matched_keywords(text, SPAM_KEYWORDS)
    is_spam = bool(spam_matches) or domain in SPAM_DOMAINS
    if is_spam:
        return HeuristicResult(
            category=EmailCategory.SPAM,
            urgency=EmailUrgency.LOW,
            status=EmailStatus.IGNORED,
            requires_human=False,
            flags={
                "is_spam": True,
                "spam_matches": spam_matches,
                "sender_domain": domain,
                "stop_reason": "spam",
            },
            action_type=ActionType.IGNORED,
            action_reason="Spam detected by keyword or sender domain reputation.",
            stop_processing=True,
        )

    is_internal = domain in INTERNAL_DOMAINS
    if is_internal:
        return HeuristicResult(
            category=EmailCategory.INTERNAL,
            urgency=EmailUrgency.LOW,
            status=EmailStatus.IGNORED,
            requires_human=False,
            flags={
                "is_internal": True,
                "sender_domain": domain,
                "stop_reason": "internal",
            },
            action_type=ActionType.IGNORED,
            action_reason="Internal email routed away from customer triage workflow.",
            stop_processing=True,
        )

    security_matches = _matched_keywords(text, SECURITY_KEYWORDS)
    critical_security_matches = _matched_keywords(text, CRITICAL_SECURITY_KEYWORDS)
    if security_matches:
        urgency = EmailUrgency.CRITICAL if critical_security_matches else EmailUrgency.HIGH
        return HeuristicResult(
            category=EmailCategory.LEGAL if "data breach" in security_matches else EmailCategory.OTHER,
            urgency=urgency,
            status=EmailStatus.ESCALATED,
            requires_human=True,
            flags={
                "is_security_threat": True,
                "is_critical_security": bool(critical_security_matches),
                "security_matches": security_matches,
                "stop_reason": "critical_security" if critical_security_matches else "security",
            },
            action_type=ActionType.ESCALATE,
            action_reason="Security threat detected; route to security queue and block auto-reply.",
            stop_processing=bool(critical_security_matches),
        )

    urgency_matches = _matched_keywords(text, URGENCY_KEYWORDS)
    legal_matches = _matched_keywords(text, LEGAL_KEYWORDS)
    urgency = _resolve_urgency(urgency_matches, legal_matches)
    category = EmailCategory.LEGAL if legal_matches else None

    return HeuristicResult(
        category=category,
        urgency=urgency,
        status=EmailStatus.PROCESSING,
        requires_human=urgency in (EmailUrgency.CRITICAL, EmailUrgency.HIGH) or bool(legal_matches),
        flags={
            "is_spam": False,
            "is_internal": False,
            "is_security_threat": False,
            "urgency_matches": urgency_matches,
            "legal_matches": legal_matches,
            "stop_reason": None,
        },
        action_type=None,
        action_reason=None,
        stop_processing=False,
    )


def _resolve_urgency(
    urgency_matches: list[str], legal_matches: list[str]
) -> EmailUrgency:
    if "p0" in urgency_matches or "cease and desist" in urgency_matches:
        return EmailUrgency.CRITICAL
    if legal_matches or urgency_matches:
        return EmailUrgency.HIGH
    return EmailUrgency.LOW


def _matched_keywords(text: str, keywords: tuple[str, ...]) -> list[str]:
    return [keyword for keyword in keywords if keyword in text]


def _sender_domain(sender: str) -> str:
    if "@" not in sender:
        return ""
    return sender.rsplit("@", 1)[1].lower()
