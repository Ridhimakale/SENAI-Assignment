from sqlalchemy import Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.enums import ClassificationValidationStatus
from app.models.mixins import TimestampMixin
from app.models.sqlalchemy_types import enum_type


class ClassificationRun(TimestampMixin, Base):
    __tablename__ = "classification_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    email_id: Mapped[int] = mapped_column(ForeignKey("emails.id"), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(100), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    classification_output: Mapped[dict | None] = mapped_column(JSONB)
    confidence: Mapped[float | None]
    validation_status: Mapped[ClassificationValidationStatus] = mapped_column(
        enum_type(
            ClassificationValidationStatus, name="classification_validation_status"
        ),
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(Text)

    email = relationship("Email", back_populates="classification_runs")


Index("ix_classification_runs_email_id", ClassificationRun.email_id)
Index("ix_classification_runs_prompt_version", ClassificationRun.prompt_version)
Index("ix_classification_runs_model_name", ClassificationRun.model_name)
