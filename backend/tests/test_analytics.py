from datetime import UTC, datetime, timedelta

import pytest

import app.db.base  # noqa: F401
from app.models.action import Action
from app.models.contact import Contact
from app.models.email import Email
from app.models.enums import ActionType, ContactStatus, EmailCategory
from app.services.analytics import service as analytics_service_module
from app.services.analytics.service import AnalyticsService


class FakeAnalyticsRepository:
    def __init__(self, session):
        self.now = datetime(2026, 1, 10, tzinfo=UTC)

    async def get_sentiment_emails(self, *, sender, since):
        return [
            Email(
                id=1,
                thread_id=1,
                contact_id=1,
                message_id="msg_1",
                sender=sender or "karen@example.com",
                body="Bad",
                timestamp=datetime(2026, 1, 1, tzinfo=UTC),
                sentiment_score=-0.4,
            ),
            Email(
                id=2,
                thread_id=1,
                contact_id=1,
                message_id="msg_2",
                sender=sender or "karen@example.com",
                body="Worse",
                timestamp=datetime(2026, 1, 2, tzinfo=UTC),
                sentiment_score=-0.7,
            ),
            Email(
                id=3,
                thread_id=1,
                contact_id=1,
                message_id="msg_3",
                sender=sender or "karen@example.com",
                body="Terrible",
                timestamp=datetime(2026, 1, 3, tzinfo=UTC),
                sentiment_score=-0.8,
            ),
        ]

    async def get_category_counts(self, *, start_date, end_date):
        return [(EmailCategory.COMPLAINT, 3), (EmailCategory.BILLING, 2)]

    async def get_response_heatmap(self, *, start_date, end_date):
        return [(9, 2), (17, 4)]

    async def get_unresolved_threads(self, *, older_than):
        return [("karen@example.com", 2, datetime.now(UTC) - timedelta(hours=60))]

    async def get_recent_negative_counts(self, *, since):
        return {"karen@example.com": 3}

    async def get_contacts_with_threads_and_emails(self):
        return [
            Contact(
                id=1,
                email="karen@example.com",
                company="Retail Co",
                status=ContactStatus.ACTIVE,
                churn_risk_score=0.91,
            )
        ]

    async def get_agent_performance(self, *, start_date, end_date):
        return {
            "action_counts": {
                ActionType.AUTO_REPLY: 2,
                ActionType.ESCALATE: 3,
                ActionType.TICKET_CREATED: 1,
            },
            "average_confidence": 0.82,
        }


@pytest.fixture(autouse=True)
def fake_repository(monkeypatch):
    monkeypatch.setattr(
        analytics_service_module, "AnalyticsRepository", FakeAnalyticsRepository
    )


@pytest.mark.asyncio
async def test_sentiment_trend_detects_three_negative_emails() -> None:
    service = AnalyticsService(session=None)  # type: ignore[arg-type]

    response = await service.sentiment_trend(sender="karen@example.com", days=30)

    assert len(response.points) == 3
    assert response.deterioration_detected is True
    assert response.consecutive_negative_count == 3
    assert response.points[-1].moving_average == pytest.approx((-0.4 - 0.7 - 0.8) / 3)


@pytest.mark.asyncio
async def test_category_breakdown_returns_counts() -> None:
    service = AnalyticsService(session=None)  # type: ignore[arg-type]

    response = await service.category_breakdown(
        start_date=datetime(2026, 1, 1, tzinfo=UTC),
        end_date=datetime(2026, 1, 31, tzinfo=UTC),
    )

    assert response.items[0].category == "Complaint"
    assert response.items[0].count == 3


@pytest.mark.asyncio
async def test_response_heatmap_returns_all_24_hours() -> None:
    service = AnalyticsService(session=None)  # type: ignore[arg-type]

    response = await service.response_heatmap(
        start_date=datetime(2026, 1, 1, tzinfo=UTC),
        end_date=datetime(2026, 1, 31, tzinfo=UTC),
    )

    assert len(response.points) == 24
    assert response.points[9].action_count == 2
    assert response.points[17].action_count == 4


@pytest.mark.asyncio
async def test_at_risk_accounts_include_churn_sentiment_and_unresolved_reasons() -> None:
    service = AnalyticsService(session=None)  # type: ignore[arg-type]

    response = await service.at_risk_accounts()

    assert response.accounts[0].sender == "karen@example.com"
    assert set(response.accounts[0].reasons) == {
        "high_churn_risk_score",
        "unresolved_threads_over_48h",
        "sentiment_deterioration",
    }


@pytest.mark.asyncio
async def test_agent_performance_rates_and_average_confidence() -> None:
    service = AnalyticsService(session=None)  # type: ignore[arg-type]

    response = await service.agent_performance(
        start_date=datetime(2026, 1, 1, tzinfo=UTC),
        end_date=datetime(2026, 1, 31, tzinfo=UTC),
    )

    assert response.total_actions == 6
    assert response.auto_reply_rate == pytest.approx(2 / 6)
    assert response.escalation_rate == pytest.approx(3 / 6)
    assert response.average_confidence_score == 0.82
