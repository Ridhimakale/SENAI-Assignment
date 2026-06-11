from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import WebIntelligenceStatus
from app.models.web_intelligence_cache import WebIntelligenceCache


class WebIntelligenceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_valid_cache(
        self, *, target_entity: str, source_url: str, now: datetime | None = None
    ) -> WebIntelligenceCache | None:
        current_time = now or datetime.now(UTC)
        result = await self.session.execute(
            select(WebIntelligenceCache)
            .where(
                WebIntelligenceCache.target_entity == target_entity,
                WebIntelligenceCache.source_url == source_url,
                WebIntelligenceCache.expires_at > current_time,
            )
            .order_by(WebIntelligenceCache.scraped_at.desc())
        )
        return result.scalars().first()

    async def save_cache(
        self,
        *,
        target_entity: str,
        source_url: str,
        source_type: str,
        scraped_data: dict,
        scraped_at: datetime,
        expires_at: datetime,
        status: WebIntelligenceStatus,
        error_message: str | None,
        robots_allowed: bool | None,
    ) -> WebIntelligenceCache:
        cache = WebIntelligenceCache(
            target_entity=target_entity,
            source_url=source_url,
            source_type=source_type,
            scraped_data=scraped_data,
            scraped_at=scraped_at,
            expires_at=expires_at,
            status=status,
            error_message=error_message,
            robots_allowed=robots_allowed,
        )
        self.session.add(cache)
        await self.session.flush()
        return cache
