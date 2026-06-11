from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, Index, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.enums import ContactStatus
from app.models.mixins import TimestampMixin
from app.models.sqlalchemy_types import enum_type


class Contact(TimestampMixin, Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(255))
    company: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[ContactStatus] = mapped_column(
        enum_type(ContactStatus, name="contact_status"),
        default=ContactStatus.ACTIVE,
        nullable=False,
    )
    vip_reason: Mapped[str | None] = mapped_column(String(255))
    account_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    churn_risk_score: Mapped[float] = mapped_column(default=0.0, nullable=False)
    subscription_tier: Mapped[str | None] = mapped_column(String(100))
    renewal_status: Mapped[str | None] = mapped_column(String(100))
    open_ticket_count: Mapped[int] = mapped_column(default=0, nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB)
    last_contact_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    threads = relationship("Thread", back_populates="contact")
    emails = relationship("Email", back_populates="contact")


Index("ix_contacts_status", Contact.status)
Index("ix_contacts_company", Contact.company)
Index("ix_contacts_churn_risk_score", Contact.churn_risk_score)
