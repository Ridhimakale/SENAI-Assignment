from app.models.email import Email
from app.models.enums import EmailCategory, EmailUrgency


def auto_reply_block_reason(email: Email) -> str | None:
    flags = email.heuristic_flags or {}
    if email.category in (EmailCategory.SPAM, EmailCategory.INTERNAL):
        return "Auto-reply blocked for spam or internal emails."
    if flags.get("is_security_threat") or flags.get("is_critical_security"):
        return "Auto-reply blocked for security threats."
    if email.urgency == EmailUrgency.CRITICAL:
        return "Auto-reply blocked for critical urgency."
    if email.category == EmailCategory.LEGAL:
        return "Auto-reply blocked for legal matters."
    if email.requires_human:
        return "Auto-reply blocked because human review is required."
    return None
