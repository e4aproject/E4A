# tests/test_api_cli_integration.py
from fastapi.testclient import TestClient
from api.server import app

client = TestClient(app)


def test_api_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_mandate_lifecycle():
    m = client.post("/mandates/create", json={"issuer": "did:ex:alice", "beneficiary": "did:ex:bob", "amount": 50})
    assert m.status_code == 200
    mid = m.json()["mandate"]["mandate_id"]
    e = client.post(f"/mandates/execute/{mid}")
    assert e.status_code == 200
    r = client.get("/reputation")
    assert "reputation" in r.json()
