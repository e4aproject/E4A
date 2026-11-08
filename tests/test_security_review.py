"""Phase 8 security-review regression tests.

Finding F1 (fixed): when an API token was configured, it gated only the
/v1 routes; the legacy surface (mandate create/execute, gates,
governance, reputation) operated on the same store with no
authentication at all. These tests pin the corrected behavior, plus two
operational properties: error responses carry no internals, and a
file-copy backup restores mandates and audit records.
"""

import shutil

import pytest
from fastapi.testclient import TestClient

from api.server import create_app

TOKEN = "phase8" + "-test-" + "token"
AUTH = {"Authorization": f"Bearer {TOKEN}"}

BODY = {
    "issuer": "did:ex:alice",
    "beneficiary": "did:ex:bob",
    "amount": 5,
    "intent": {
        "goal": "security review regression",
        "expected_outcome": "legacy surface gated by the same token as /v1",
        "contextual_tone": "neutral",
        "statistical_purpose": "phase 8 evidence",
    },
}


@pytest.fixture()
def secured_client(tmp_path):
    app = create_app(db_path=str(tmp_path / "secured.db"), api_token=TOKEN)
    with TestClient(app) as client:
        yield client


def test_legacy_surface_requires_the_token(secured_client):
    assert secured_client.post("/mandates/create", json=BODY).status_code == 401
    assert secured_client.get("/gates/pending").status_code == 401
    assert secured_client.get("/reputation").status_code == 401
    assert (
        secured_client.post("/governance/propose", json={"id": "p1", "action": "a", "description": "d"}).status_code
        == 401
    )


def test_legacy_surface_works_with_the_token(secured_client):
    created = secured_client.post("/mandates/create", json=BODY, headers=AUTH)
    assert created.status_code == 200
    mandate_id = created.json()["mandate"]["mandate_id"]
    executed = secured_client.post(f"/mandates/execute/{mandate_id}", headers=AUTH)
    assert executed.status_code == 200


def test_health_and_ready_stay_open_for_probes(secured_client):
    assert secured_client.get("/health").status_code == 200
    ready = secured_client.get("/ready")
    assert ready.status_code == 200
    assert ready.json()["auth_required"] is True


def test_error_envelope_carries_no_internals(secured_client):
    response = secured_client.get("/v1/mandates/no-such-id", headers=AUTH)
    assert response.status_code == 404
    body = response.json()
    assert set(body.keys()) == {"error"}
    assert set(body["error"].keys()) == {"code", "message"}
    raw = response.text.lower()
    assert "traceback" not in raw and "site-packages" not in raw and ".py" not in raw


def test_backup_restore_by_file_copy(tmp_path):
    source = tmp_path / "live.db"
    backup = tmp_path / "backup.db"
    app = create_app(db_path=str(source))
    with TestClient(app) as client:
        created = client.post("/v1/mandates", json={**BODY, "replay_nonce": "backup-1"})
        assert created.status_code == 201
        mandate_id = created.json()["mandate_id"]

    shutil.copyfile(source, backup)  # the documented backup operation

    restored = create_app(db_path=str(backup))
    with TestClient(restored) as client:
        fetched = client.get(f"/v1/mandates/{mandate_id}")
        assert fetched.status_code == 200
        audit = client.get(f"/v1/mandates/{mandate_id}/audit")
        assert audit.status_code == 200
        assert any(e["entry_type"] == "mandate_created" for e in audit.json())
