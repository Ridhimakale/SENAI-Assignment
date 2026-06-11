from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.enums import ThreadStatus
from app.models.mixins import TimestampMixin
from app.models.sqlalchemy_types import enum_type


class Thread(TimestampMixin, Base):
    __tablename__ = "threads"
    __table_args__ = (
        UniqueConstraint("thread_id", "sender_email", name="uq_threads_thread_sender"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    thread_id: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(500))
    sender_email: Mapped[str] = mapped_column(String(320), nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[ThreadStatus] = mapped_column(
        enum_type(ThreadStatus, name="thread_status"),
        default=ThreadStatus.OPEN,
        nullable=False,
    )
    assigned_to: Mapped[str | None] = mapped_column(String(255))
    priority_score: Mapped[int] = mapped_column(default=0, nullable=False)
    message_count: Mapped[int] = mapped_column(default=0, nullable=False)
    last_sentiment_score: Mapped[float | None]

    contact = relationship("Contact", back_populates="threads")
    emails = relationship("Email", back_populates="thread", cascade="all, delete-orphan")
    tickets = relationship("InternalTicket", back_populates="thread")


Index("ix_threads_sender_email", Thread.sender_email)
Index("ix_threads_contact_id", Thread.contact_id)
Index("ix_threads_status", Thread.status)
Index("ix_threads_last_updated_at", Thread.last_updated_at)
