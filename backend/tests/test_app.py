from fastapi.testclient import TestClient

from app.main import create_app


def test_health_check_returns_success_envelope() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "ok"
