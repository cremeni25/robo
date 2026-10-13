from fastapi.testclient import TestClient
from core_v1.app.main import app


def test_invitation_route_requires_ingest_key(monkeypatch):
    monkeypatch.setenv("CORE_INGEST_KEY", "test-only-key")
    with TestClient(app) as client:
        response = client.post("/v1/awin/discovery/invitation-triage", json={
            "advertiser": "World Businesses for Sale",
            "commission_base_percent": "20",
            "commission_bonus_percent": "10",
            "terms_available": True,
        })
    assert response.status_code == 401


def test_invitation_route_never_auto_approves(monkeypatch):
    monkeypatch.setenv("CORE_INGEST_KEY", "test-only-key")
    with TestClient(app) as client:
        response = client.post(
            "/v1/awin/discovery/invitation-triage",
            headers={"x-core-ingest-key": "test-only-key"},
            json={"advertiser": "World Businesses for Sale", "terms_available": True},
        )
    assert response.status_code == 200
    assert response.json()["publication_ready"] is False
    assert response.json()["membership"] == "unverified"
