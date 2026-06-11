from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import quote_plus, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import WebIntelligenceStatus
from app.repositories.web_intelligence import WebIntelligenceRepository
from app.schemas.web_intelligence import ReputationResponse, ReputationSource

CACHE_TTL = timedelta(hours=6)
USER_AGENT = "SenAI-CRM-Intelligence/1.0"


@dataclass(frozen=True)
class ScrapeTarget:
    source: str
    source_type: str
    url: str


class WebIntelligenceService:
    def __init__(self, session: AsyncSession | None = None) -> None:
        self.session = session
        self.repository = WebIntelligenceRepository(session) if session is not None else None

    async def get_reputation(self, company: str) -> ReputationResponse:
        targets = _build_targets(company)
        sources = await asyncio.gather(
            *(self._fetch_source(company=company, target=target) for target in targets)
        )
        summary = _summarize_sources(sources)
        return ReputationResponse(
            company=company,
            sources=sources,
            summary=summary,
            market_intelligence_block=_market_intelligence_block(company, sources, summary),
        )

    async def _fetch_source(self, *, company: str, target: ScrapeTarget) -> ReputationSource:
        now = datetime.now(UTC)
        if self.repository is not None:
            cached = await self.repository.get_valid_cache(
                target_entity=company, source_url=target.url, now=now
            )
            if cached is not None:
                data = cached.scraped_data or {}
                return ReputationSource(
                    source=target.source,
                    source_url=target.url,
                    rating=data.get("rating"),
                    recent_review_count=data.get("recent_review_count"),
                    common_themes=data.get("common_themes", []),
                    cached=True,
                    status=cached.status.value,
                    error_message=cached.error_message,
                    robots_allowed=cached.robots_allowed,
                    expires_at=cached.expires_at,
                )

        robots_allowed = await robots_txt_allows(target.url)
        if not robots_allowed:
            source = ReputationSource(
                source=target.source,
                source_url=target.url,
                common_themes=[],
                cached=False,
                status=WebIntelligenceStatus.SKIPPED_ROBOTS.value,
                error_message="Blocked by robots.txt policy.",
                robots_allowed=False,
                expires_at=now + CACHE_TTL,
            )
            await self._save(company, target, source, now)
            return source

        try:
            async with httpx.AsyncClient(timeout=8, headers={"User-Agent": USER_AGENT}) as client:
                response = await client.get(target.url)
                response.raise_for_status()
            parsed = _parse_reputation_page(target.source, target.url, response.text)
            source = ReputationSource(
                source=target.source,
                source_url=target.url,
                rating=parsed["rating"],
                recent_review_count=parsed["recent_review_count"],
                common_themes=parsed["common_themes"],
                cached=False,
                status=WebIntelligenceStatus.SUCCESS.value,
                robots_allowed=True,
                expires_at=now + CACHE_TTL,
            )
            await self._save(company, target, source, now)
            return source
        except Exception as exc:
            source = ReputationSource(
                source=target.source,
                source_url=target.url,
                common_themes=[],
                cached=False,
                status=WebIntelligenceStatus.FAILED.value,
                error_message=str(exc),
                robots_allowed=True,
                expires_at=now + CACHE_TTL,
            )
            await self._save(company, target, source, now)
            return source

    async def _save(
        self, company: str, target: ScrapeTarget, source: ReputationSource, now: datetime
    ) -> None:
        if self.repository is None:
            return
        await self.repository.save_cache(
            target_entity=company,
            source_url=target.url,
            source_type=target.source_type,
            scraped_data={
                "rating": source.rating,
                "recent_review_count": source.recent_review_count,
                "common_themes": source.common_themes,
            },
            scraped_at=now,
            expires_at=source.expires_at or now + CACHE_TTL,
            status=WebIntelligenceStatus(source.status),
            error_message=source.error_message,
            robots_allowed=source.robots_allowed,
        )
        await self.session.flush()  # type: ignore[union-attr]


async def robots_txt_allows(url: str) -> bool:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return False
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    def check() -> bool:
        parser = RobotFileParser()
        parser.set_url(robots_url)
        try:
            parser.read()
            return parser.can_fetch(USER_AGENT, url)
        except Exception:
            return False

    return await asyncio.to_thread(check)


def _build_targets(company: str) -> list[ScrapeTarget]:
    slug = _slug(company)
    quoted = quote_plus(company)
    return [
        ScrapeTarget(
            source="Trustpilot",
            source_type="Review",
            url=f"https://www.trustpilot.com/review/{slug}.com",
        ),
        ScrapeTarget(
            source="G2",
            source_type="Review",
            url=f"https://www.g2.com/search?query={quoted}",
        ),
        ScrapeTarget(
            source="CompetitorPricing",
            source_type="Competitor",
            url=f"https://www.google.com/search?q={quoted}+competitor+pricing",
        ),
    ]


def _slug(company: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", company.lower()).strip("-") or "unknown"


def _parse_reputation_page(source: str, source_url: str, html: str) -> dict:
    text = re.sub(r"\s+", " ", html)
    rating = _first_float(
        (
            r"([0-5](?:\.\d)?)\s*(?:out of|/)\s*5",
            r"ratingValue['\"]?\s*[:=]\s*['\"]?([0-5](?:\.\d)?)",
        ),
        text,
    )
    review_count = _first_int(
        (
            r"([0-9][0-9,]*)\s+reviews",
            r"reviewCount['\"]?\s*[:=]\s*['\"]?([0-9][0-9,]*)",
        ),
        text,
    )
    themes = [
        theme
        for theme in ("support", "billing", "pricing", "reliability", "onboarding")
        if theme in text.lower()
    ][:3]
    return {
        "rating": rating,
        "recent_review_count": review_count,
        "common_themes": themes,
        "source_url": source_url,
        "source": source,
    }


def _first_float(patterns: tuple[str, ...], text: str) -> float | None:
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1).replace(",", ""))
    return None


def _first_int(patterns: tuple[str, ...], text: str) -> int | None:
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1).replace(",", ""))
    return None


def _summarize_sources(sources: list[ReputationSource]) -> str:
    successful = [source for source in sources if source.status == WebIntelligenceStatus.SUCCESS.value]
    if not successful:
        return "Live public intelligence is currently unavailable; proceed using internal context."
    ratings = [source.rating for source in successful if source.rating is not None]
    themes = sorted({theme for source in successful for theme in source.common_themes})
    rating_text = f" Average rating {sum(ratings) / len(ratings):.1f}/5." if ratings else ""
    theme_text = f" Common themes: {', '.join(themes)}." if themes else ""
    return f"Public intelligence retrieved from {len(successful)} source(s).{rating_text}{theme_text}"


def _market_intelligence_block(
    company: str, sources: list[ReputationSource], summary: str
) -> str:
    lines = [f"Market Intelligence for {company}:", summary]
    for source in sources:
        lines.append(
            f"- {source.source}: status={source.status}, rating={source.rating}, "
            f"reviews={source.recent_review_count}, cached={source.cached}"
        )
    return "\n".join(lines)


def create_web_intelligence_service(
    session: AsyncSession | None = None,
) -> WebIntelligenceService:
    return WebIntelligenceService(session=session)
