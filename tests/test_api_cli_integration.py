# tests/test_api_cli_integration.py
from fastapi.testclient import TestClient
from api.server import create_app
import pytest

@pytest.fixture(scope="function")
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c

def test_api_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_mandate_lifecycle(client):
    m = client.post("/mandates/create", json={
        "issuer": "did:ex:alice",
        "beneficiary": "did:ex:bob",
        "amount": 50,
        "intent": {
            "goal": "test mandate lifecycle",
            "expected_outcome": "mandate created and executed",
            "contextual_tone": "neutral",
            "statistical_purpose": "validate API flow"
        }
    })
    assert m.status_code == 200
    mid = m.json()["mandate"]["mandate_id"]
    e = client.post(f"/mandates/execute/{mid}")
    assert e.status_code == 200
    r = client.get("/reputation")
    assert "reputation" in r.json()
