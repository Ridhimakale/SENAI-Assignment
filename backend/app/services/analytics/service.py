from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ActionType
from app.repositories.analytics import AnalyticsRepository, default_since
from app.schemas.analytics import (
    AgentPerformanceResponse,
    AtRiskAccount,
    AtRiskAccountsResponse,
    CategoryBreakdownItem,
    CategoryBreakdownResponse,
    ResponseHeatmapPoint,
    ResponseHeatmapResponse,
    SentimentTrendPoint,
    SentimentTrendResponse,
)


@dataclass
class AnalyticsService:
    session: AsyncSession

    async def sentiment_trend(
        self, *, sender: str | None = None, days: int = 30
    ) -> SentimentTrendResponse:
        repository = AnalyticsRepository(self.session)
        emails = await repository.get_sentiment_emails(
            sender=sender, since=default_since(days)
        )
        points: list[SentimentTrendPoint] = []
        scores: list[float] = []
        for email in emails:
            score = float(email.sentiment_score)
            scores.append(score)
            window = scores[-3:]
            moving_average = sum(window) / len(window)
            points.append(
                SentimentTrendPoint(
                    timestamp=email.timestamp,
                    sender=email.sender if sender is None else None,
                    sentiment_score=score,
                    moving_average=moving_average,
                )
            )

        consecutive_negative_count = _consecutive_negative_count_from_scores(scores)
        return SentimentTrendResponse(
            sender=sender,
            points=points,
            deterioration_detected=consecutive_negative_count >= 3,
            consecutive_negative_count=consecutive_negative_count,
        )

    async def category_breakdown(
        self, *, start_date: datetime, end_date: datetime
    ) -> CategoryBreakdownResponse:
        repository = AnalyticsRepository(self.session)
        rows = await repository.get_category_counts(
            start_date=start_date, end_date=end_date
        )
        return CategoryBreakdownResponse(
            items=[
                CategoryBreakdownItem(category=category.value, count=count)
                for category, count in rows
            ]
        )

    async def response_heatmap(
        self, *, start_date: datetime, end_date: datetime
    ) -> ResponseHeatmapResponse:
        repository = AnalyticsRepository(self.session)
        counts = dict(
            await repository.get_response_heatmap(start_date=start_date, end_date=end_date)
        )
        return ResponseHeatmapResponse(
            points=[
                ResponseHeatmapPoint(hour_of_day=hour, action_count=counts.get(hour, 0))
                for hour in range(24)
            ]
        )

    async def at_risk_accounts(self) -> AtRiskAccountsResponse:
        repository = AnalyticsRepository(self.session)
        unresolved_cutoff = datetime.now(UTC) - timedelta(hours=48)
        unresolved_rows = await repository.get_unresolved_threads(
            older_than=unresolved_cutoff
        )
        negative_counts = await repository.get_recent_negative_counts(
            since=datetime.now(UTC) - timedelta(days=30)
        )
        unresolved_by_sender = {
            sender: (count, oldest) for sender, count, oldest in unresolved_rows
        }

        accounts: list[AtRiskAccount] = []
        contacts = await repository.get_contacts_with_threads_and_emails()
        for contact in contacts:
            unresolved_count, oldest = unresolved_by_sender.get(contact.email, (0, None))
            consecutive_negative_count = negative_counts.get(contact.email, 0)
            reasons: list[str] = []
            if contact.churn_risk_score >= 0.7:
                reasons.append("high_churn_risk_score")
            if unresolved_count > 0:
                reasons.append("unresolved_threads_over_48h")
            if consecutive_negative_count >= 3:
                reasons.append("sentiment_deterioration")

            if reasons:
                oldest_hours = None
                if oldest is not None:
                    oldest_hours = (
                        datetime.now(UTC) - _as_utc(oldest)
                    ).total_seconds() / 3600
                accounts.append(
                    AtRiskAccount(
                        sender=contact.email,
                        company=contact.company,
                        churn_risk_score=contact.churn_risk_score,
                        unresolved_threads=unresolved_count,
                        oldest_unresolved_hours=oldest_hours,
                        consecutive_negative_count=consecutive_negative_count,
                        reasons=reasons,
                    )
                )
        return AtRiskAccountsResponse(accounts=accounts)

    async def agent_performance(
        self, *, start_date: datetime, end_date: datetime
    ) -> AgentPerformanceResponse:
        repository = AnalyticsRepository(self.session)
        data = await repository.get_agent_performance(
            start_date=start_date, end_date=end_date
        )
        counts = data["action_counts"]
        total_actions = sum(counts.values())
        auto_reply_count = counts.get(ActionType.AUTO_REPLY, 0)
        escalation_count = counts.get(ActionType.ESCALATE, 0)
        return AgentPerformanceResponse(
            total_actions=total_actions,
            auto_reply_count=auto_reply_count,
            escalation_count=escalation_count,
            auto_reply_rate=_safe_rate(auto_reply_count, total_actions),
            escalation_rate=_safe_rate(escalation_count, total_actions),
            average_confidence_score=data["average_confidence"],
        )


def _safe_rate(count: int, total: int) -> float:
    if total == 0:
        return 0.0
    return count / total


def _consecutive_negative_count_from_scores(scores: list[float]) -> int:
    count = 0
    for score in reversed(scores):
        if score < -0.2:
            count += 1
        else:
            break
    return count


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
