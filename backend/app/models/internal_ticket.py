from sqlalchemy import Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.enums import TicketStatus
from app.models.mixins import TimestampMixin
from app.models.sqlalchemy_types import enum_type


class InternalTicket(TimestampMixin, Base):
    __tablename__ = "internal_tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    email_id: Mapped[int] = mapped_column(ForeignKey("emails.id"), nullable=False)
    thread_id: Mapped[int] = mapped_column(ForeignKey("threads.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    assignee: Mapped[str | None] = mapped_column(String(255))
    priority: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[TicketStatus] = mapped_column(
        enum_type(TicketStatus, name="ticket_status"),
        default=TicketStatus.OPEN,
        nullable=False,
    )
    created_by: Mapped[str] = mapped_column(String(255), default="agent", nullable=False)

    email = relationship("Email", back_populates="tickets")
    thread = relationship("Thread", back_populates="tickets")


Index("ix_internal_tickets_email_id", InternalTicket.email_id)
Index("ix_internal_tickets_thread_id", InternalTicket.thread_id)
Index("ix_internal_tickets_status", InternalTicket.status)
Index("ix_internal_tickets_priority", InternalTicket.priority)
