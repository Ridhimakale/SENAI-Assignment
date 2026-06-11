import asyncio
from datetime import UTC, datetime
import json

from fastapi.testclient import TestClient

from app.api.v1.simulation import get_simulation_service
from app.main import create_app
from app.schemas.ingestion import EmailIngestResponse
from app.schemas.simulation import EmailStreamSimulationRequest, EmailStreamSimulationResponse
from app.services.simulation.service import EmailStreamSimulatorService


class FakeIngestionService:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def ingest_email(self, request):
        self.calls.append(request.message_id)
        return EmailIngestResponse(
            job_id=f"job_{request.message_id}",
            email_id=len(self.calls),
            message_id=request.message_id,
            deduplicated=False,
            status="Queued",
            priority_score=10,
        )


class FakeSimulationService:
    def __init__(self) -> None:
        self.ingestion_service = FakeIngestionService()

    async def run(self, request: EmailStreamSimulationRequest) -> EmailStreamSimulationResponse:
        return EmailStreamSimulationResponse(
            source_path=request.source_path,
            total_loaded=2,
            processed=2,
            succeeded=2,
            failed=0,
            deduplicated=0,
            elapsed_seconds=0.0,
            replay_rate_per_second=request.emails_per_second,
            results=[],
        )


def test_simulation_endpoint_returns_success_envelope(tmp_path) -> None:
    dataset = tmp_path / "email-data-advanced.json"
    dataset.write_text(
        json.dumps(
            [
                {
                    "message_id": "msg_001",
                    "thread_id": "thread_a",
                    "sender": "alice@example.com",
                    "subject": "Hello",
                    "body": "Test",
                    "timestamp": datetime(2026, 1, 1, tzinfo=UTC).isoformat(),
                },
                {
                    "message_id": "msg_002",
                    "thread_id": "thread_a",
                    "sender": "alice@example.com",
                    "subject": "Follow up",
                    "body": "More text",
                    "timestamp": datetime(2026, 1, 2, tzinfo=UTC).isoformat(),
                },
            ]
        ),
        encoding="utf-8",
    )

    app = create_app()
    app.dependency_overrides[get_simulation_service] = lambda: FakeSimulationService()
    client = TestClient(app)

    response = client.post(
        "/api/simulate/stream",
        json={
            "source_path": str(dataset),
            "emails_per_second": 50,
            "dry_run": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["processed"] == 2
    assert payload["data"]["succeeded"] == 2


def test_simulation_service_replays_json_file(tmp_path) -> None:
    dataset = tmp_path / "email-data-advanced.json"
    dataset.write_text(
        json.dumps(
            [
                {
                    "message_id": "msg_001",
                    "thread_id": "thread_a",
                    "sender": "alice@example.com",
                    "subject": "Hello",
                    "body": "Test",
                    "timestamp": datetime(2026, 1, 1, tzinfo=UTC).isoformat(),
                },
                {
                    "message_id": "msg_002",
                    "thread_id": "thread_a",
                    "sender": "alice@example.com",
                    "subject": "Follow up",
                    "body": "More text",
                    "timestamp": datetime(2026, 1, 2, tzinfo=UTC).isoformat(),
                },
            ]
        ),
        encoding="utf-8",
    )

    class FakeReplayIngestionService:
        async def ingest_email(self, request):
            return EmailIngestResponse(
                job_id=f"job_{request.message_id}",
                email_id=1,
                message_id=request.message_id,
                deduplicated=request.message_id == "msg_002",
                status="Queued",
                priority_score=10,
            )

    service = EmailStreamSimulatorService(ingestion_service=FakeReplayIngestionService())
    result = asyncio.run(
        service.run(
            EmailStreamSimulationRequest(
                source_path=str(dataset),
                emails_per_second=1000,
            )
        )
    )

    assert result.total_loaded == 2
    assert result.processed == 2
    assert result.succeeded == 2
    assert result.deduplicated == 1
