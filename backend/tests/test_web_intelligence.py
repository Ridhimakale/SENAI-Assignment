from datetime import UTC, datetime

import pytest

from app.models.email import Email
from app.models.enums import EmailCategory, EmailUrgency
from app.services.web_intelligence import service as web_service
from app.services.web_intelligence.service import (
    ScrapeTarget,
    WebIntelligenceService,
    _parse_reputation_page,
)
from app.services.web_intelligence.triggers import should_trigger_web_intelligence


def make_email(
    *,
    subject: str,
    body: str,
    category: EmailCategory | None = None,
    urgency: EmailUrgency | None = None,
    sentiment_score: float | None = None,
    flags: dict | None = None,
) -> Email:
    return Email(
        id=1,
        thread_id=1,
        contact_id=1,
        message_id="msg_web",
        sender="karen.w@retail-co.com",
        subject=subject,
        body=body,
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        category=category,
        urgency=urgency,
        sentiment_score=sentiment_score,
        heuristic_flags=flags,
    )


def test_web_intelligence_triggers_on_review_terms() -> None:
    email = make_email(
        subject="Public review",
        body="I will post publicly on Trustpilot and G2.",
    )

    result = should_trigger_web_intelligence(email)

    assert result.triggered is True
    assert any(reason.startswith("public_signal_terms") for reason in result.reasons)


def test_web_intelligence_triggers_on_negative_sentiment() -> None:
    email = make_email(subject="Complaint", body="Terrible support.", sentiment_score=-0.8)

    result = should_trigger_web_intelligence(email)

    assert result.triggered is True
    assert "sentiment_below_-0.6" in result.reasons


def test_web_intelligence_triggers_on_high_urgency_complaint() -> None:
    email = make_email(
        subject="Complaint",
        body="This is urgent.",
        category=EmailCategory.COMPLAINT,
        urgency=EmailUrgency.HIGH,
    )

    result = should_trigger_web_intelligence(email)

    assert result.triggered is True
    assert "high_urgency_complaint" in result.reasons


def test_reputation_parser_extracts_rating_and_reviews() -> None:
    parsed = _parse_reputation_page(
        "Trustpilot",
        "https://example.com",
        "RatingValue: 4.2 reviewCount: 125 reviews mention support and billing",
    )

    assert parsed["rating"] == 4.2
    assert parsed["recent_review_count"] == 125
    assert "support" in parsed["common_themes"]
    assert "billing" in parsed["common_themes"]


@pytest.mark.asyncio
async def test_service_gracefully_handles_robots_block(monkeypatch) -> None:
    async def blocked(url: str) -> bool:
        return False

    monkeypatch.setattr(web_service, "robots_txt_allows", blocked)
    service = WebIntelligenceService(session=None)

    source = await service._fetch_source(
        company="Retail Co",
        target=ScrapeTarget(
            source="Trustpilot",
            source_type="Review",
            url="https://example.com/review/retail-co",
        ),
    )

    assert source.status == "SkippedRobots"
    assert source.robots_allowed is False


@pytest.mark.asyncio
async def test_service_returns_reputation_response_when_scrapes_fail(monkeypatch) -> None:
    async def allowed(url: str) -> bool:
        return True

    class FailingClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def get(self, url):
            raise RuntimeError("network unavailable")

    monkeypatch.setattr(web_service, "robots_txt_allows", allowed)
    monkeypatch.setattr(web_service.httpx, "AsyncClient", lambda *args, **kwargs: FailingClient())
    service = WebIntelligenceService(session=None)

    response = await service.get_reputation("Retail Co")

    assert response.company == "Retail Co"
    assert response.sources
    assert all(source.status == "Failed" for source in response.sources)
    assert "unavailable" in response.summary.lower()
