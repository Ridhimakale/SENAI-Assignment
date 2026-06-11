from app.models.email import Email
from app.schemas.rag import RagSearchResponse


def build_classification_prompt(
    *,
    current_email: Email,
    thread_history: list[Email],
    rag_context: RagSearchResponse,
) -> str:
    thread_text = "\n".join(
        f"- [{email.timestamp.isoformat()}] {email.sender}: {email.subject or '(no subject)'}\n{email.body}"
        for email in thread_history
    )
    rag_text = "\n\n".join(
        f"Source: {result.source_doc} | Score: {result.score:.3f}\n{result.chunk_text}"
        for result in rag_context.results
    )
    return f"""
You are classifying a customer email for a CRM intelligence platform.

Use the full thread history and the retrieved internal policy context.
Resolve conflicting signals by prioritizing safety, legal/compliance risk, churn risk, and the customer's latest intent.
If confidence is below 0.70, requires_human must be true.
Suggested replies must cite the policy source document when policy context is used.

Return only JSON with this schema:
{{
  "category": "Complaint|Inquiry|Bug Report|Feature Request|Compliance|Legal|Billing|Spam|Internal|Other",
  "sentiment": "Positive|Neutral|Negative|Mixed",
  "sentiment_score": -1.0,
  "urgency": "Critical|High|Medium|Low",
  "requires_human": true,
  "escalation_reason": "string or null",
  "suggested_reply": "string or null",
  "confidence": 0.0,
  "detected_entities": {{
    "order_ids": [],
    "ticket_ids": [],
    "monetary_amounts": [],
    "deadlines": [],
    "products_mentioned": []
  }}
}}

Current email:
Sender: {current_email.sender}
Subject: {current_email.subject or "(no subject)"}
Body:
{current_email.body}

Full thread history:
{thread_text}

Retrieved policy context:
{rag_text}
""".strip()
