from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.enums import WebIntelligenceStatus
from app.models.mixins import TimestampMixin
from app.models.sqlalchemy_types import enum_type


class WebIntelligenceCache(TimestampMixin, Base):
    __tablename__ = "web_intelligence_cache"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    target_entity: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(100), nullable=False)
    scraped_data: Mapped[dict | None] = mapped_column(JSONB)
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[WebIntelligenceStatus] = mapped_column(
        enum_type(WebIntelligenceStatus, name="web_intelligence_status"),
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(Text)
    robots_allowed: Mapped[bool | None] = mapped_column(Boolean)


Index("ix_web_intelligence_target_entity", WebIntelligenceCache.target_entity)
Index("ix_web_intelligence_source_url", WebIntelligenceCache.source_url)
Index("ix_web_intelligence_expires_at", WebIntelligenceCache.expires_at)
Index(
    "ix_web_intelligence_target_expires",
    WebIntelligenceCache.target_entity,
    WebIntelligenceCache.expires_at,
)
