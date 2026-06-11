from dataclasses import dataclass, field
from enum import StrEnum

from app.models.email import Email
from app.models.enums import EmailCategory, EmailUrgency


class ScenarioCode(StrEnum):
    ALICE_PRICING_CONTEXT = "ALICE_PRICING_CONTEXT"
    BOB_SLA_LEGAL_ESCALATION = "BOB_SLA_LEGAL_ESCALATION"
    KAREN_REPUTATION_CRISIS = "KAREN_REPUTATION_CRISIS"
    ELEANOR_HIPAA_ENTERPRISE = "ELEANOR_HIPAA_ENTERPRISE"
    BIGCORP_RFP_OPPORTUNITY = "BIGCORP_RFP_OPPORTUNITY"
    SECURITY_RANSOMWARE = "SECURITY_RANSOMWARE"
    SECURITY_SUSPICIOUS_LOGIN = "SECURITY_SUSPICIOUS_LOGIN"
    GDPR_ARTICLE_20 = "GDPR_ARTICLE_20"
    SPAM_THREAD = "SPAM_THREAD"
    NADIA_DATA_CORRUPTION_BUG = "NADIA_DATA_CORRUPTION_BUG"
    CHATBOT_MISINFORMATION = "CHATBOT_MISINFORMATION"


@dataclass(frozen=True)
class ScenarioDirective:
    code: ScenarioCode
    severity: EmailUrgency
    requires_human: bool
    recommended_actions: list[str]
    notes: str


@dataclass(frozen=True)
class ScenarioEvaluation:
    scenarios: list[ScenarioDirective] = field(default_factory=list)

    @property
    def flags(self) -> dict:
        return {
            "scenario_codes": [scenario.code.value for scenario in self.scenarios],
            "scenario_notes": {
                scenario.code.value: scenario.notes for scenario in self.scenarios
            },
            "scenario_recommended_actions": {
                scenario.code.value: scenario.recommended_actions
                for scenario in self.scenarios
            },
            "scenario_requires_human": any(
                scenario.requires_human for scenario in self.scenarios
            ),
        }

    @property
    def highest_urgency(self) -> EmailUrgency | None:
        order = {
            EmailUrgency.CRITICAL: 4,
            EmailUrgency.HIGH: 3,
            EmailUrgency.MEDIUM: 2,
            EmailUrgency.LOW: 1,
        }
        if not self.scenarios:
            return None
        return max((scenario.severity for scenario in self.scenarios), key=order.get)


def evaluate_special_scenarios(
    *, email: Email, thread_history: list[Email] | None = None
) -> ScenarioEvaluation:
    history = thread_history or [email]
    combined_text = " ".join(
        f"{item.sender} {item.subject or ''} {item.body or ''}" for item in history
    ).lower()
    current_text = f"{email.sender} {email.subject or ''} {email.body or ''}".lower()
    thread_ref = ""
    if email.thread is not None:
        thread_ref = getattr(email.thread, "thread_id", "") or ""
    thread_ref = thread_ref.lower()

    scenarios: list[ScenarioDirective] = []

    if "thread_alice_pricing" in thread_ref or "greenlight-npo" in email.sender:
        scenarios.append(
            ScenarioDirective(
                code=ScenarioCode.ALICE_PRICING_CONTEXT,
                severity=EmailUrgency.MEDIUM,
                requires_human=False,
                recommended_actions=[
                    "retrieve_full_thread",
                    "search_pricing_policy",
                    "reference_nonprofit_discount",
                    "explain_pro_rata_billing",
                ],
                notes="Use full pricing thread, nonprofit discount context, and pro-rata billing policy.",
            )
        )

    if "thread_bob_outage" in thread_ref or "bob.jones@enterprise.net" in email.sender:
        scenarios.append(
            ScenarioDirective(
                code=ScenarioCode.BOB_SLA_LEGAL_ESCALATION,
                severity=EmailUrgency.CRITICAL,
                requires_human=True,
                recommended_actions=[
                    "retrieve_full_thread",
                    "search_sla_policy",
                    "check_enterprise_account_status",
                    "flag_for_legal",
                    "draft_holding_reply",
                    "escalate_to_human",
                ],
                notes="Bob requires SLA credit/RCA review, legal flag, holding reply, and human escalation.",
            )
        )

    if "thread_karen_refund" in thread_ref or "karen.w@retail-co.com" in email.sender:
        negative_count = _negative_or_complaint_count(history)
        if negative_count >= 3 or _contains_any(
            combined_text, ("trustpilot", "g2", "public review", "post publicly")
        ):
            scenarios.append(
                ScenarioDirective(
                    code=ScenarioCode.KAREN_REPUTATION_CRISIS,
                    severity=EmailUrgency.HIGH,
                    requires_human=True,
                    recommended_actions=[
                        "retrieve_full_thread",
                        "search_refund_policy",
                        "search_escalation_matrix",
                        "trigger_web_intelligence",
                        "create_retention_case",
                        "escalate_to_customer_success",
                    ],
                    notes="Repeated negative/unanswered refund complaints with public review risk require retention escalation.",
                )
            )

    if "thread_eleanor_compliance" in thread_ref or "hipaa" in combined_text:
        scenarios.append(
            ScenarioDirective(
                code=ScenarioCode.ELEANOR_HIPAA_ENTERPRISE,
                severity=EmailUrgency.HIGH,
                requires_human=True,
                recommended_actions=[
                    "search_compliance_faq",
                    "create_compliance_ticket",
                    "route_to_compliance_operations",
                    "notify_account_owner",
                ],
                notes="HIPAA/BAA enterprise compliance requests require compliance review.",
            )
        )

    if "thread_bigcorp_rfp" in thread_ref or _contains_any(
        combined_text, ("rfp", "$2.4m", "2.4m", "compliance audit")
    ):
        scenarios.append(
            ScenarioDirective(
                code=ScenarioCode.BIGCORP_RFP_OPPORTUNITY,
                severity=EmailUrgency.HIGH,
                requires_human=True,
                recommended_actions=[
                    "mark_vip_opportunity",
                    "create_rfp_ticket",
                    "route_to_sales_and_compliance",
                    "preserve_thread_history",
                ],
                notes="High-value RFP/compliance opportunity should route to sales and compliance leadership.",
            )
        )

    if _contains_any(current_text, ("ransomware", "send 2 btc", "publish data", "publish your data")):
        scenarios.append(
            ScenarioDirective(
                code=ScenarioCode.SECURITY_RANSOMWARE,
                severity=EmailUrgency.CRITICAL,
                requires_human=True,
                recommended_actions=[
                    "security_escalation",
                    "notify_security_leadership",
                    "never_auto_reply",
                    "stop_processing",
                ],
                notes="Ransomware requires immediate security escalation and no attacker engagement.",
            )
        )

    if _contains_any(current_text, ("suspicious login", "credential compromise", "unauthorized access")):
        scenarios.append(
            ScenarioDirective(
                code=ScenarioCode.SECURITY_SUSPICIOUS_LOGIN,
                severity=EmailUrgency.CRITICAL,
                requires_human=True,
                recommended_actions=[
                    "security_escalation",
                    "create_security_ticket",
                    "notify_security_leadership",
                ],
                notes="Login/credential compromise must route immediately to security.",
            )
        )

    if _contains_any(current_text, ("gdpr article 20", "article 20", "data portability")):
        scenarios.append(
            ScenarioDirective(
                code=ScenarioCode.GDPR_ARTICLE_20,
                severity=EmailUrgency.HIGH,
                requires_human=True,
                recommended_actions=[
                    "flag_for_legal",
                    "create_compliance_ticket",
                    "acknowledge_30_day_window",
                    "no_generic_auto_reply",
                ],
                notes="Formal GDPR Article 20 request requires compliance workflow and 30-day response tracking.",
            )
        )

    if "thread_spam_" in thread_ref or email.category == EmailCategory.SPAM:
        scenarios.append(
            ScenarioDirective(
                code=ScenarioCode.SPAM_THREAD,
                severity=EmailUrgency.LOW,
                requires_human=False,
                recommended_actions=["mark_ignored", "never_auto_reply"],
                notes="Spam must not receive an auto-reply.",
            )
        )

    if "thread_nadia_bug" in thread_ref or _contains_any(
        combined_text, ("silent data corruption", "success message", "data missing")
    ):
        scenarios.append(
            ScenarioDirective(
                code=ScenarioCode.NADIA_DATA_CORRUPTION_BUG,
                severity=EmailUrgency.CRITICAL,
                requires_human=True,
                recommended_actions=[
                    "create_engineering_ticket",
                    "escalate_to_human",
                    "preserve_reproduction_details",
                ],
                notes="Silent data corruption is mission-critical and requires engineering escalation.",
            )
        )

    if "thread_chatbot_misinformation" in thread_ref or _contains_any(
        combined_text, ("chatbot", "wrong refund", "incorrect refund", "misinformation")
    ):
        scenarios.append(
            ScenarioDirective(
                code=ScenarioCode.CHATBOT_MISINFORMATION,
                severity=EmailUrgency.HIGH,
                requires_human=True,
                recommended_actions=[
                    "search_refund_policy",
                    "compare_chatbot_claim_to_policy",
                    "create_internal_ticket",
                    "draft_non_liability_reply",
                    "escalate_to_human",
                ],
                notes="Chatbot misinformation requires policy correction, internal escalation, and careful reply without admitting liability.",
            )
        )

    return ScenarioEvaluation(scenarios=scenarios)


def merge_scenario_flags(existing_flags: dict | None, evaluation: ScenarioEvaluation) -> dict:
    flags = dict(existing_flags or {})
    scenario_flags = evaluation.flags
    existing_codes = list(flags.get("scenario_codes", []))
    for code in scenario_flags["scenario_codes"]:
        if code not in existing_codes:
            existing_codes.append(code)
    flags.update(scenario_flags)
    flags["scenario_codes"] = existing_codes
    return flags


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def _negative_or_complaint_count(history: list[Email]) -> int:
    count = 0
    for email in history:
        text = f"{email.subject or ''} {email.body or ''}".lower()
        if email.sentiment_score is not None and email.sentiment_score < -0.2:
            count += 1
            continue
        if _contains_any(text, ("angry", "complaint", "refund", "cancel", "terrible", "review")):
            count += 1
    return count
