"""initial foundation schema

Revision ID: 20260610_0001
Revises:
Create Date: 2026-06-10 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from app.models.vector_type import Vector

revision: str = "20260610_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


contact_status = postgresql.ENUM(
    "VIP", "Blocked", "Active", "Churned", name="contact_status", create_type=False
)
thread_status = postgresql.ENUM(
    "Open", "Resolved", "Escalated", "Ignored", name="thread_status", create_type=False
)
email_status = postgresql.ENUM(
    "Received", "Processing", "Replied", "Escalated", "Ignored", name="email_status", create_type=False
)
email_category = postgresql.ENUM(
    "Complaint",
    "Inquiry",
    "Bug Report",
    "Feature Request",
    "Compliance",
    "Legal",
    "Billing",
    "Spam",
    "Internal",
    "Other",
    name="email_category",
    create_type=False,
)
email_urgency = postgresql.ENUM(
    "Critical", "High", "Medium", "Low", name="email_urgency", create_type=False
)
action_type = postgresql.ENUM(
    "Auto-Reply", "Escalate", "Legal-Flag", "Ticket-Created", "Ignored", name="action_type", create_type=False
)
action_status = postgresql.ENUM(
    "Proposed", "Executed", "Blocked", "Failed", name="action_status", create_type=False
)
job_status = postgresql.ENUM(
    "Queued", "Processing", "Completed", "Failed", "Skipped", name="job_status", create_type=False
)
ticket_status = postgresql.ENUM("Open", "InProgress", "Resolved", name="ticket_status", create_type=False)
classification_validation_status = postgresql.ENUM(
    "Valid", "Invalid", "Repaired", "Failed", name="classification_validation_status", create_type=False
)
web_intelligence_status = postgresql.ENUM(
    "Success", "Failed", "SkippedRobots", name="web_intelligence_status", create_type=False
)


def upgrade() -> None:
    bind = op.get_bind()
    for enum_type in (
        contact_status,
        thread_status,
        email_status,
        email_category,
        email_urgency,
        action_type,
        action_status,
        job_status,
        ticket_status,
        classification_validation_status,
        web_intelligence_status,
    ):
        enum_type.create(bind, checkfirst=True)

    op.create_table(
        "contacts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("name", sa.String(length=255)),
        sa.Column("company", sa.String(length=255)),
        sa.Column("status", contact_status, nullable=False),
        sa.Column("vip_reason", sa.String(length=255)),
        sa.Column("account_value", sa.Numeric(12, 2)),
        sa.Column("churn_risk_score", sa.Float(), nullable=False),
        sa.Column("subscription_tier", sa.String(length=100)),
        sa.Column("renewal_status", sa.String(length=100)),
        sa.Column("open_ticket_count", sa.Integer(), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB()),
        sa.Column("last_contact_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_contacts_status", "contacts", ["status"])
    op.create_index("ix_contacts_company", "contacts", ["company"])
    op.create_index("ix_contacts_churn_risk_score", "contacts", ["churn_risk_score"])

    op.create_table(
        "processing_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_id", sa.String(length=100), nullable=False),
        sa.Column("status", job_status, nullable=False),
        sa.Column("stage", sa.String(length=100), nullable=False),
        sa.Column("error_code", sa.String(length=100)),
        sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("job_id"),
    )
    op.create_index("ix_processing_jobs_status", "processing_jobs", ["status"])
    op.create_index("ix_processing_jobs_stage", "processing_jobs", ["stage"])

    op.create_table(
        "threads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("thread_id", sa.String(length=255), nullable=False),
        sa.Column("contact_id", sa.Integer(), sa.ForeignKey("contacts.id"), nullable=False),
        sa.Column("subject", sa.String(length=500)),
        sa.Column("sender_email", sa.String(length=320), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", thread_status, nullable=False),
        sa.Column("assigned_to", sa.String(length=255)),
        sa.Column("priority_score", sa.Integer(), nullable=False),
        sa.Column("message_count", sa.Integer(), nullable=False),
        sa.Column("last_sentiment_score", sa.Float()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("thread_id", "sender_email", name="uq_threads_thread_sender"),
    )
    op.create_index("ix_threads_sender_email", "threads", ["sender_email"])
    op.create_index("ix_threads_contact_id", "threads", ["contact_id"])
    op.create_index("ix_threads_status", "threads", ["status"])
    op.create_index("ix_threads_last_updated_at", "threads", ["last_updated_at"])

    op.create_table(
        "emails",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("thread_id", sa.Integer(), sa.ForeignKey("threads.id"), nullable=False),
        sa.Column("contact_id", sa.Integer(), sa.ForeignKey("contacts.id"), nullable=False),
        sa.Column("processing_job_id", sa.Integer(), sa.ForeignKey("processing_jobs.id")),
        sa.Column("message_id", sa.String(length=255), nullable=False),
        sa.Column("sender", sa.String(length=320), nullable=False),
        sa.Column("subject", sa.String(length=500)),
        sa.Column("normalized_subject", sa.String(length=500)),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("body_preview", sa.String(length=500)),
        sa.Column("body_truncated", sa.Boolean(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sentiment_score", sa.Float()),
        sa.Column("category", email_category),
        sa.Column("urgency", email_urgency),
        sa.Column("requires_human", sa.Boolean(), nullable=False),
        sa.Column("confidence", sa.Float()),
        sa.Column("raw_entities", postgresql.JSONB()),
        sa.Column("status", email_status, nullable=False),
        sa.Column("priority_score", sa.Integer(), nullable=False),
        sa.Column("heuristic_flags", postgresql.JSONB()),
        sa.Column("classification_raw", postgresql.JSONB()),
        sa.Column("classification_error", sa.Text()),
        sa.Column("rag_context", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("message_id"),
    )
    op.create_index("ix_emails_thread_timestamp", "emails", ["thread_id", "timestamp"])
    op.create_index("ix_emails_sender_timestamp", "emails", ["sender", "timestamp"])
    op.create_index("ix_emails_status", "emails", ["status"])
    op.create_index("ix_emails_category", "emails", ["category"])
    op.create_index("ix_emails_urgency", "emails", ["urgency"])
    op.create_index("ix_emails_requires_human", "emails", ["requires_human"])
    op.create_index("ix_emails_priority_score", "emails", ["priority_score"])
    op.create_index("ix_emails_sentiment_score", "emails", ["sentiment_score"])

    op.create_table(
        "actions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email_id", sa.Integer(), sa.ForeignKey("emails.id"), nullable=False),
        sa.Column("agent_reasoning_log", postgresql.JSONB()),
        sa.Column("action_type", action_type, nullable=False),
        sa.Column("proposed_content", sa.Text()),
        sa.Column("is_approved", sa.Boolean(), nullable=False),
        sa.Column("approved_by", sa.String(length=255)),
        sa.Column("executed_at", sa.DateTime(timezone=True)),
        sa.Column("status", action_status, nullable=False),
        sa.Column("safety_block_reason", sa.Text()),
        sa.Column("tool_name", sa.String(length=255)),
        sa.Column("tool_input", postgresql.JSONB()),
        sa.Column("tool_output", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_actions_email_id", "actions", ["email_id"])
    op.create_index("ix_actions_action_type", "actions", ["action_type"])
    op.create_index("ix_actions_status", "actions", ["status"])
    op.create_index("ix_actions_executed_at", "actions", ["executed_at"])

    op.create_table(
        "classification_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email_id", sa.Integer(), sa.ForeignKey("emails.id"), nullable=False),
        sa.Column("prompt_version", sa.String(length=100), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("classification_output", postgresql.JSONB()),
        sa.Column("confidence", sa.Float()),
        sa.Column("validation_status", classification_validation_status, nullable=False),
        sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_classification_runs_email_id", "classification_runs", ["email_id"])
    op.create_index("ix_classification_runs_prompt_version", "classification_runs", ["prompt_version"])
    op.create_index("ix_classification_runs_model_name", "classification_runs", ["model_name"])

    op.create_table(
        "internal_tickets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email_id", sa.Integer(), sa.ForeignKey("emails.id"), nullable=False),
        sa.Column("thread_id", sa.Integer(), sa.ForeignKey("threads.id"), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("assignee", sa.String(length=255)),
        sa.Column("priority", sa.String(length=50), nullable=False),
        sa.Column("status", ticket_status, nullable=False),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_internal_tickets_email_id", "internal_tickets", ["email_id"])
    op.create_index("ix_internal_tickets_thread_id", "internal_tickets", ["thread_id"])
    op.create_index("ix_internal_tickets_status", "internal_tickets", ["status"])
    op.create_index("ix_internal_tickets_priority", "internal_tickets", ["priority"])

    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_doc", sa.String(length=255), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("embedding_model", sa.String(length=255), nullable=False),
        sa.Column("embedding_hash", sa.String(length=255)),
        sa.Column("faiss_vector_id", sa.Integer()),
        sa.Column("embedding", Vector(384)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("source_doc", "chunk_index", name="uq_knowledge_source_chunk"),
    )
    op.create_index("ix_knowledge_chunks_source_doc", "knowledge_chunks", ["source_doc"])
    op.create_index("ix_knowledge_chunks_faiss_vector_id", "knowledge_chunks", ["faiss_vector_id"])

    op.create_table(
        "web_intelligence_cache",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_url", sa.String(length=1000), nullable=False),
        sa.Column("target_entity", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=100), nullable=False),
        sa.Column("scraped_data", postgresql.JSONB()),
        sa.Column("scraped_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", web_intelligence_status, nullable=False),
        sa.Column("error_message", sa.Text()),
        sa.Column("robots_allowed", sa.Boolean()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_web_intelligence_target_entity", "web_intelligence_cache", ["target_entity"])
    op.create_index("ix_web_intelligence_source_url", "web_intelligence_cache", ["source_url"])
    op.create_index("ix_web_intelligence_expires_at", "web_intelligence_cache", ["expires_at"])
    op.create_index("ix_web_intelligence_target_expires", "web_intelligence_cache", ["target_entity", "expires_at"])

    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("performed_by", sa.String(length=255), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("diff", postgresql.JSONB()),
        sa.Column("request_id", sa.String(length=100)),
        sa.Column("correlation_id", sa.String(length=100)),
        sa.Column("metadata_json", postgresql.JSONB()),
    )
    op.create_index("ix_audit_entity", "audit_log", ["entity_type", "entity_id"])
    op.create_index("ix_audit_timestamp", "audit_log", ["timestamp"])
    op.create_index("ix_audit_performed_by", "audit_log", ["performed_by"])


def downgrade() -> None:
    op.drop_index("ix_audit_performed_by", table_name="audit_log")
    op.drop_index("ix_audit_timestamp", table_name="audit_log")
    op.drop_index("ix_audit_entity", table_name="audit_log")
    op.drop_table("audit_log")

    op.drop_index("ix_web_intelligence_target_expires", table_name="web_intelligence_cache")
    op.drop_index("ix_web_intelligence_expires_at", table_name="web_intelligence_cache")
    op.drop_index("ix_web_intelligence_source_url", table_name="web_intelligence_cache")
    op.drop_index("ix_web_intelligence_target_entity", table_name="web_intelligence_cache")
    op.drop_table("web_intelligence_cache")

    op.drop_index("ix_knowledge_chunks_faiss_vector_id", table_name="knowledge_chunks")
    op.drop_index("ix_knowledge_chunks_source_doc", table_name="knowledge_chunks")
    op.drop_table("knowledge_chunks")

    op.drop_index("ix_internal_tickets_priority", table_name="internal_tickets")
    op.drop_index("ix_internal_tickets_status", table_name="internal_tickets")
    op.drop_index("ix_internal_tickets_thread_id", table_name="internal_tickets")
    op.drop_index("ix_internal_tickets_email_id", table_name="internal_tickets")
    op.drop_table("internal_tickets")

    op.drop_index("ix_classification_runs_model_name", table_name="classification_runs")
    op.drop_index("ix_classification_runs_prompt_version", table_name="classification_runs")
    op.drop_index("ix_classification_runs_email_id", table_name="classification_runs")
    op.drop_table("classification_runs")

    op.drop_index("ix_actions_executed_at", table_name="actions")
    op.drop_index("ix_actions_status", table_name="actions")
    op.drop_index("ix_actions_action_type", table_name="actions")
    op.drop_index("ix_actions_email_id", table_name="actions")
    op.drop_table("actions")

    op.drop_index("ix_emails_sentiment_score", table_name="emails")
    op.drop_index("ix_emails_priority_score", table_name="emails")
    op.drop_index("ix_emails_requires_human", table_name="emails")
    op.drop_index("ix_emails_urgency", table_name="emails")
    op.drop_index("ix_emails_category", table_name="emails")
    op.drop_index("ix_emails_status", table_name="emails")
    op.drop_index("ix_emails_sender_timestamp", table_name="emails")
    op.drop_index("ix_emails_thread_timestamp", table_name="emails")
    op.drop_table("emails")

    op.drop_index("ix_threads_last_updated_at", table_name="threads")
    op.drop_index("ix_threads_status", table_name="threads")
    op.drop_index("ix_threads_contact_id", table_name="threads")
    op.drop_index("ix_threads_sender_email", table_name="threads")
    op.drop_table("threads")

    op.drop_index("ix_processing_jobs_stage", table_name="processing_jobs")
    op.drop_index("ix_processing_jobs_status", table_name="processing_jobs")
    op.drop_table("processing_jobs")

    op.drop_index("ix_contacts_churn_risk_score", table_name="contacts")
    op.drop_index("ix_contacts_company", table_name="contacts")
    op.drop_index("ix_contacts_status", table_name="contacts")
    op.drop_table("contacts")

    bind = op.get_bind()
    for enum_type in (
        web_intelligence_status,
        classification_validation_status,
        ticket_status,
        job_status,
        action_status,
        action_type,
        email_urgency,
        email_category,
        email_status,
        thread_status,
        contact_status,
    ):
        enum_type.drop(bind, checkfirst=True)
