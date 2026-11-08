"""Integration tests for the protocol 1.0 reference service (spec section 11).

Covers the full lifecycle over HTTP, the error envelope and status mapping,
the token gate, and — the Phase 5 gate — restart persistence: a second app
instance on the same SQLite file sees mandates, gate state, and audit
records exactly as the first left them.
"""

import pytest
from fastapi.testclient import TestClient

from api.server import create_app

INTENT = {
    "goal": "demonstrate the v1 API lifecycle",
    "expected_outcome": "mandate executed via HTTP",
    "contextual_tone": "neutral",
    "statistical_purpose": "api integration test",
}

FULL = {
    "issuer": "did:ex:alice",
    "beneficiary": "did:ex:bob",
    "amount": 10,
    "currency": "USD",
    "replay_nonce": "api-nonce-1",
    "intent": {**INTENT, "requires_approval": ["did:ex:carol", "did:ex:dave"]},
}

SIMPLE = {"issuer": "did:ex:alice", "beneficiary": "did:ex:bob", "intent": INTENT}


@pytest.fixture()
def client(tmp_path):
    app = create_app(db_path=str(tmp_path / "e4a.db"))
    with TestClient(app) as c:
        yield c


def test_health_and_ready(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"
    r = client.get("/ready")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ready"
    assert body["protocol_version"] == "1.0"
    assert body["persistent"] is True


def test_full_lifecycle_over_http(client):
    r = client.post("/v1/mandates", json=FULL)
    assert r.status_code == 201, r.text
    mandate = r.json()
    assert mandate["status"] == "pending_approval"
    mid = mandate["mandate_id"]

    # Execution blocked while the gate is pending
    r = client.post(f"/v1/mandates/{mid}/execute")
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "E4A_APPROVAL_REQUIRED"

    # Unauthorized approver
    r = client.post(f"/v1/mandates/{mid}/decisions", json={"actor": "did:ex:mallory", "decision": "approve"})
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "E4A_UNAUTHORIZED_APPROVER"

    # Both required approvals
    r = client.post(f"/v1/mandates/{mid}/decisions", json={"actor": "did:ex:carol", "decision": "approve"})
    assert r.status_code == 200 and r.json()["status"] == "pending_approval"
    r = client.post(f"/v1/mandates/{mid}/decisions", json={"actor": "did:ex:dave", "decision": "approve"})
    assert r.status_code == 200 and r.json()["status"] == "approved"

    # Execute, then double-execute fails
    r = client.post(f"/v1/mandates/{mid}/execute")
    assert r.status_code == 200
    assert r.json()["status"] == "executed"
    assert r.json()["result"]["mock"] is True
    r = client.post(f"/v1/mandates/{mid}/execute")
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "E4A_INVALID_TRANSITION"

    # Audit trail over HTTP
    r = client.get(f"/v1/mandates/{mid}/audit")
    assert r.status_code == 200
    types = [e["entry_type"] for e in r.json()]
    for expected in ("mandate_created", "gate_created", "approval_recorded", "gate_approved", "mandate_executed"):
        assert expected in types, types


def test_validation_and_not_found_envelopes(client):
    r = client.post("/v1/mandates", json={"issuer": "did:ex:alice", "beneficiary": "did:ex:bob"})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "E4A_VALIDATION_FAILED"

    r = client.get("/v1/mandates/nope")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "E4A_NOT_FOUND"


def test_idempotent_create_and_nonce_conflict_over_http(client):
    r1 = client.post("/v1/mandates", json=FULL)
    r2 = client.post("/v1/mandates", json=FULL)
    assert r1.status_code == 201 and r2.status_code == 201
    assert r1.json()["mandate_id"] == r2.json()["mandate_id"]

    conflicting = dict(FULL, amount=999)
    r3 = client.post("/v1/mandates", json=conflicting)
    assert r3.status_code == 409
    assert r3.json()["error"]["code"] == "E4A_NONCE_CONFLICT"


def test_restart_persistence(tmp_path):
    """Phase 5 gate: restart the service; state must remain consistent."""
    db = str(tmp_path / "e4a.db")

    app1 = create_app(db_path=db)
    with TestClient(app1) as c1:
        r = c1.post("/v1/mandates", json=FULL)
        assert r.status_code == 201
        mid = r.json()["mandate_id"]
        r = c1.post(f"/v1/mandates/{mid}/decisions", json={"actor": "did:ex:carol", "decision": "approve"})
        assert r.status_code == 200

    app2 = create_app(db_path=db)
    with TestClient(app2) as c2:
        r = c2.get(f"/v1/mandates/{mid}")
        assert r.status_code == 200
        assert r.json()["status"] == "pending_approval"

        r = c2.post(f"/v1/mandates/{mid}/decisions", json={"actor": "did:ex:dave", "decision": "approve"})
        assert r.status_code == 200 and r.json()["status"] == "approved"

        r = c2.post(f"/v1/mandates/{mid}/execute")
        assert r.status_code == 200 and r.json()["status"] == "executed"

        r = c2.get(f"/v1/mandates/{mid}/audit")
        assert r.status_code == 200
        assert len(r.json()) >= 5


def test_token_gate(tmp_path):
    app = create_app(db_path=str(tmp_path / "e4a.db"), api_token="s3cret")
    with TestClient(app) as c:
        r = c.post("/v1/mandates", json=SIMPLE)
        assert r.status_code == 401
        r = c.post("/v1/mandates", json=SIMPLE, headers={"Authorization": "Bearer wrong"})
        assert r.status_code == 401
        r = c.post("/v1/mandates", json=SIMPLE, headers={"Authorization": "Bearer s3cret"})
        assert r.status_code == 201
        # Health stays open so orchestrators can probe liveness.
        assert c.get("/health").status_code == 200
        ready = c.get("/ready")
        assert ready.status_code == 200 and ready.json()["auth_required"] is True
