from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.enums import ActionStatus, ActionType
from app.models.mixins import TimestampMixin


class Action(TimestampMixin, Base):
    __tablename__ = "actions"

    id: Mapped[int] = mapped_column(primary_key=True)
    email_id: Mapped[int] = mapped_column(ForeignKey("emails.id"), nullable=False)
    agent_reasoning_log: Mapped[list | dict | None] = mapped_column(JSONB)
    action_type: Mapped[ActionType] = mapped_column(
        Enum(ActionType, name="action_type"), nullable=False
    )
    proposed_content: Mapped[str | None] = mapped_column(Text)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    approved_by: Mapped[str | None] = mapped_column(String(255))
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[ActionStatus] = mapped_column(
        Enum(ActionStatus, name="action_status"),
        default=ActionStatus.PROPOSED,
        nullable=False,
    )
    safety_block_reason: Mapped[str | None] = mapped_column(Text)
    tool_name: Mapped[str | None] = mapped_column(String(255))
    tool_input: Mapped[dict | None] = mapped_column(JSONB)
    tool_output: Mapped[dict | None] = mapped_column(JSONB)

    email = relationship("Email", back_populates="actions")


Index("ix_actions_email_id", Action.email_id)
Index("ix_actions_action_type", Action.action_type)
Index("ix_actions_status", Action.status)
Index("ix_actions_executed_at", Action.executed_at)
