from sqlalchemy import Enum, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.enums import JobStatus
from app.models.mixins import TimestampMixin
from app.models.sqlalchemy_types import enum_type


class ProcessingJob(TimestampMixin, Base):
    __tablename__ = "processing_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    status: Mapped[JobStatus] = mapped_column(
        enum_type(JobStatus, name="job_status"),
        default=JobStatus.QUEUED,
        nullable=False,
    )
    stage: Mapped[str] = mapped_column(String(100), default="INGESTED", nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(100))
    error_message: Mapped[str | None] = mapped_column(Text)

    email = relationship("Email", back_populates="processing_job", uselist=False)


Index("ix_processing_jobs_status", ProcessingJob.status)
Index("ix_processing_jobs_stage", ProcessingJob.stage)
