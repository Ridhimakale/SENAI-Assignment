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
You are a CRM triage classifier for a customer support operations platform.

Task:
Classify the current email using the full thread history and the retrieved policy context.
Do not take actions. Only understand the message and produce the structured classification output.

Guidance:
- Use the latest message in the thread as the primary signal, but keep earlier thread messages in mind.
- Use retrieved policy context to ground billing, refund, SLA, legal, compliance, and escalation decisions.
- When signals conflict, prioritize safety, legal/compliance risk, security risk, and churn risk.
- If the email is ambiguous, reflect that in the confidence score and escalation reason.
- If confidence is below 0.70, set requires_human to true.
- If policy context informs the suggested reply, mention the source document in the reply text.
- Return only valid JSON. No markdown. No explanation outside the JSON object.

Output schema:
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
