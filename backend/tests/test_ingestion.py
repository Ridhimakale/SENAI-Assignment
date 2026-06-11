from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.api.v1.ingest import get_ingestion_service
from app.main import create_app
from app.schemas.ingestion import EmailIngestRequest, EmailIngestResponse
from app.services.ingestion.normalization import normalize_email_body
from app.services.ingestion.priority import calculate_priority_score


class FakeIngestionService:
    async def ingest_email(self, request: EmailIngestRequest) -> EmailIngestResponse:
        return EmailIngestResponse(
            job_id="job_test",
            email_id=123,
            message_id=request.message_id,
            deduplicated=False,
            status="Queued",
            priority_score=42,
        )

    async def get_status(self, job_id: str):
        return None


def test_ingest_endpoint_returns_success_envelope() -> None:
    app = create_app()
    app.dependency_overrides[get_ingestion_service] = lambda: FakeIngestionService()
    client = TestClient(app)

    response = client.post(
        "/api/ingest",
        json={
            "message_id": "msg_001",
            "thread_id": "thread_alice_pricing",
            "sender": "alice.smith@greenlight-npo.org",
            "subject": "Pricing question",
            "body": "Can you explain nonprofit pricing?",
            "timestamp": datetime(2026, 1, 14, 10, 30, tzinfo=UTC).isoformat(),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["job_id"] == "job_test"
    assert payload["data"]["message_id"] == "msg_001"


def test_ingest_rejects_blank_message_id() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/ingest",
        json={
            "message_id": " ",
            "thread_id": "thread_test",
            "sender": "sender@example.com",
            "subject": "",
            "body": "",
            "timestamp": datetime(2026, 1, 14, 10, 30, tzinfo=UTC).isoformat(),
        },
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["error_code"] == "VALIDATION_ERROR"


def test_normalize_email_body_handles_whitespace_and_html_entities() -> None:
    normalized = normalize_email_body("&nbsp;   ")

    assert normalized.body == ""
    assert normalized.preview == ""
    assert normalized.is_empty is True


def test_normalize_email_body_marks_long_content_for_later_llm_handling() -> None:
    normalized = normalize_email_body("x" * 10_001)

    assert normalized.is_truncated_for_llm is True
    assert len(normalized.preview) == 500


def test_priority_score_detects_high_risk_keywords() -> None:
    score, flags = calculate_priority_score(
        "URGENT legal escalation",
        "This is a P0 outage and we may post on Trustpilot.",
    )

    assert score == 100
    assert "urgent" in flags["matched_priority_keywords"]
    assert "legal" in flags["matched_priority_keywords"]
    assert "p0" in flags["matched_priority_keywords"]
