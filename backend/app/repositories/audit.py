from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_event(
        self,
        *,
        entity_type: str,
        entity_id: int,
        action: str,
        performed_by: str = "agent",
        diff: dict | None = None,
        correlation_id: str | None = None,
        metadata: dict | None = None,
    ) -> AuditLog:
        event = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            performed_by=performed_by,
            timestamp=datetime.now(UTC),
            diff=diff or {},
            correlation_id=correlation_id,
            metadata_json=metadata or {},
        )
        self.session.add(event)
        await self.session.flush()
        return event
