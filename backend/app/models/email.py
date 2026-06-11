from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.classification_run import ClassificationRun
from app.models.internal_ticket import InternalTicket
from app.models.enums import EmailCategory, EmailStatus, EmailUrgency
from app.models.mixins import TimestampMixin
from app.models.sqlalchemy_types import enum_type


class Email(TimestampMixin, Base):
    __tablename__ = "emails"

    id: Mapped[int] = mapped_column(primary_key=True)
    thread_id: Mapped[int] = mapped_column(ForeignKey("threads.id"), nullable=False)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"), nullable=False)
    processing_job_id: Mapped[int | None] = mapped_column(ForeignKey("processing_jobs.id"))
    message_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    sender: Mapped[str] = mapped_column(String(320), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(500))
    normalized_subject: Mapped[str | None] = mapped_column(String(500))
    body: Mapped[str] = mapped_column(Text, nullable=False)
    body_preview: Mapped[str | None] = mapped_column(String(500))
    body_truncated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sentiment_score: Mapped[float | None]
    category: Mapped[EmailCategory | None] = mapped_column(
        enum_type(EmailCategory, name="email_category")
    )
    urgency: Mapped[EmailUrgency | None] = mapped_column(
        enum_type(EmailUrgency, name="email_urgency")
    )
    requires_human: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    confidence: Mapped[float | None]
    raw_entities: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[EmailStatus] = mapped_column(
        enum_type(EmailStatus, name="email_status"),
        default=EmailStatus.RECEIVED,
        nullable=False,
    )
    priority_score: Mapped[int] = mapped_column(default=0, nullable=False)
    heuristic_flags: Mapped[dict | None] = mapped_column(JSONB)
    classification_raw: Mapped[dict | None] = mapped_column(JSONB)
    classification_error: Mapped[str | None] = mapped_column(Text)
    rag_context: Mapped[dict | None] = mapped_column(JSONB)

    thread = relationship("Thread", back_populates="emails")
    contact = relationship("Contact", back_populates="emails")
    processing_job = relationship("ProcessingJob", back_populates="email")
    actions = relationship("Action", back_populates="email", cascade="all, delete-orphan")
    classification_runs = relationship(
        "ClassificationRun", back_populates="email", cascade="all, delete-orphan"
    )
    tickets = relationship("InternalTicket", back_populates="email")


Index("ix_emails_thread_timestamp", Email.thread_id, Email.timestamp)
Index("ix_emails_sender_timestamp", Email.sender, Email.timestamp)
Index("ix_emails_status", Email.status)
Index("ix_emails_category", Email.category)
Index("ix_emails_urgency", Email.urgency)
Index("ix_emails_requires_human", Email.requires_human)
Index("ix_emails_priority_score", Email.priority_score)
Index("ix_emails_sentiment_score", Email.sentiment_score)
