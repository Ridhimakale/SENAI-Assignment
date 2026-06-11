from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action import Action
from app.models.contact import Contact
from app.models.email import Email
from app.models.enums import ActionType, EmailCategory, ThreadStatus
from app.models.thread import Thread


class AnalyticsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_sentiment_emails(
        self, *, sender: str | None, since: datetime
    ) -> list[Email]:
        query = (
            select(Email)
            .where(Email.timestamp >= since, Email.sentiment_score.is_not(None))
            .order_by(Email.timestamp.asc())
        )
        if sender:
            query = query.where(Email.sender == sender)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_category_counts(
        self, *, start_date: datetime, end_date: datetime
    ) -> list[tuple[EmailCategory, int]]:
        result = await self.session.execute(
            select(Email.category, func.count(Email.id))
            .where(
                Email.timestamp >= start_date,
                Email.timestamp <= end_date,
                Email.category.is_not(None),
            )
            .group_by(Email.category)
            .order_by(func.count(Email.id).desc())
        )
        return [(category, count) for category, count in result.all()]

    async def get_response_heatmap(
        self, *, start_date: datetime, end_date: datetime
    ) -> list[tuple[int, int]]:
        result = await self.session.execute(
            select(func.extract("hour", Action.executed_at), func.count(Action.id))
            .where(
                Action.executed_at.is_not(None),
                Action.executed_at >= start_date,
                Action.executed_at <= end_date,
            )
            .group_by(func.extract("hour", Action.executed_at))
            .order_by(func.extract("hour", Action.executed_at))
        )
        return [(int(hour), count) for hour, count in result.all()]

    async def get_contacts_with_threads_and_emails(self) -> list[Contact]:
        result = await self.session.execute(select(Contact).order_by(Contact.email.asc()))
        return list(result.scalars().all())

    async def get_unresolved_threads(self, *, older_than: datetime) -> list[tuple[str, int, datetime]]:
        result = await self.session.execute(
            select(Thread.sender_email, func.count(Thread.id), func.min(Thread.first_seen_at))
            .where(
                Thread.status.in_([ThreadStatus.OPEN, ThreadStatus.ESCALATED]),
                Thread.first_seen_at <= older_than,
            )
            .group_by(Thread.sender_email)
        )
        return [(sender, count, oldest) for sender, count, oldest in result.all()]

    async def get_recent_negative_counts(self, *, since: datetime) -> dict[str, int]:
        emails = await self.get_sentiment_emails(sender=None, since=since)
        counts: dict[str, int] = {}
        grouped: dict[str, list[Email]] = {}
        for email in emails:
            grouped.setdefault(email.sender, []).append(email)
        for sender, sender_emails in grouped.items():
            counts[sender] = _consecutive_negative_count(sender_emails)
        return counts

    async def get_agent_performance(self, *, start_date: datetime, end_date: datetime) -> dict:
        action_result = await self.session.execute(
            select(Action.action_type, func.count(Action.id))
            .where(Action.created_at >= start_date, Action.created_at <= end_date)
            .group_by(Action.action_type)
        )
        action_counts = {action_type: count for action_type, count in action_result.all()}

        confidence_result = await self.session.execute(
            select(func.avg(Email.confidence)).where(
                Email.timestamp >= start_date,
                Email.timestamp <= end_date,
                Email.confidence.is_not(None),
            )
        )
        average_confidence = confidence_result.scalar_one_or_none()
        return {
            "action_counts": action_counts,
            "average_confidence": float(average_confidence)
            if average_confidence is not None
            else None,
        }


def default_since(days: int) -> datetime:
    return datetime.now(UTC) - timedelta(days=days)


def _consecutive_negative_count(emails: list[Email]) -> int:
    count = 0
    for email in reversed(emails):
        if email.sentiment_score is not None and email.sentiment_score < -0.2:
            count += 1
        else:
            break
    return count
