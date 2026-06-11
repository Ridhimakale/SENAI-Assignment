from datetime import UTC, datetime
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.v1.operations import get_operations_service
from app.main import create_app
from app.models.enums import ActionStatus, ActionType, ContactStatus
from app.schemas.operations import ContactProfileResponse, DashboardStatsResponse


class FakeOperationsService:
    async def get_dashboard_stats(self) -> DashboardStatsResponse:
        return DashboardStatsResponse(
            pending=2,
            replied=3,
            escalated=1,
            critical=1,
            spam=4,
            needs_human=5,
        )

    async def get_contact_profile(self, email: str) -> ContactProfileResponse:
        return ContactProfileResponse(
            id=1,
            email=email,
            name="Karen",
            company="Retail Co",
            status=ContactStatus.VIP,
            vip_reason="High Revenue",
            account_value="250000.00",
            churn_risk_score=0.82,
            subscription_tier="Enterprise",
            renewal_status="At Risk",
            open_ticket_count=2,
            open_threads=1,
            last_contact_at=datetime(2026, 1, 1, tzinfo=UTC),
        )

    async def approve_draft(self, draft_id: int, approved_by: str):
        if draft_id == 99:
            raise ValueError("Auto-reply blocked for legal matters.")
        return SimpleNamespace(
            id=draft_id,
            email_id=10,
            action_type=ActionType.AUTO_REPLY,
            status=ActionStatus.EXECUTED,
            proposed_content="Approved response",
            is_approved=True,
            approved_by=approved_by,
            executed_at=datetime(2026, 1, 1, tzinfo=UTC),
            safety_block_reason=None,
            agent_reasoning_log=[],
            tool_name=None,
            tool_input=None,
            tool_output=None,
        )


def make_client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_operations_service] = lambda: FakeOperationsService()
    return TestClient(app)


def test_dashboard_stats_endpoint_is_wired() -> None:
    response = make_client().get("/dashboard/stats")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["pending"] == 2
    assert payload["data"]["needs_human"] == 5


def test_contact_profile_endpoint_is_wired() -> None:
    response = make_client().get("/contacts/karen.w@retail-co.com")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["status"] == "VIP"
    assert payload["data"]["churn_risk_score"] == 0.82


def test_blocked_draft_approval_returns_error_envelope() -> None:
    response = make_client().post("/drafts/99/approve", json={"approved_by": "manager"})

    assert response.status_code == 409
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["error_code"] == "DRAFT_BLOCKED"
