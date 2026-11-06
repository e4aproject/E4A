"""Protocol 1.0 conformance tests for the reference SDK.

Driven by the machine-readable vectors in docs/protocol/test-vectors/:
- schema vectors are checked both against the canonical schema directly and
  through the MandateEngine submission path (error codes included);
- lifecycle vectors L1-L8 are implemented as explicit scenarios below, one
  test per vector, following the steps in lifecycle-vectors.json;
- the bundled package schema must be identical to the normative document
  schema (docs/protocol/mandate.schema.json).
"""

import json
from pathlib import Path

import pytest
from jsonschema import Draft7Validator

from e4a_sdk import errors
from e4a_sdk.mandate_engine import MandateEngine, MandateEngineError
from e4a_sdk.schema import MANDATE_SCHEMA
from e4a_sdk.store import SQLiteStore

ROOT = Path(__file__).resolve().parents[1]
VECTORS = ROOT / "docs" / "protocol" / "test-vectors"


def _load(name):
    return json.loads((VECTORS / name).read_text())


SCHEMA_VECTOR_FILES = sorted(
    p.name for p in VECTORS.glob("*.json") if p.name != "lifecycle-vectors.json"
)


@pytest.mark.parametrize("filename", SCHEMA_VECTOR_FILES)
def test_schema_vector_direct(filename):
    vector = _load(filename)
    validator = Draft7Validator(MANDATE_SCHEMA)
    errs = list(validator.iter_errors(vector["mandate"]))
    if vector["expect"] == "valid":
        assert errs == [], f"{filename}: expected valid, got {[e.message for e in errs]}"
    else:
        assert errs != [], f"{filename}: expected invalid, but it validated"


@pytest.mark.parametrize("filename", SCHEMA_VECTOR_FILES)
def test_schema_vector_via_engine(filename):
    vector = _load(filename)
    engine = MandateEngine()
    if vector["expect"] == "valid":
        created = engine.create_mandate(vector["mandate"])
        assert created["mandate_id"]
    else:
        with pytest.raises(MandateEngineError) as excinfo:
            engine.create_mandate(vector["mandate"])
        assert excinfo.value.code == vector["error_code"], filename


def test_bundled_schema_matches_normative_document():
    document_schema = json.loads((ROOT / "docs" / "protocol" / "mandate.schema.json").read_text())
    assert MANDATE_SCHEMA == document_schema


# ----------------------------------------------------------------------
# Lifecycle vectors (docs/protocol/test-vectors/lifecycle-vectors.json)
# ----------------------------------------------------------------------

def _body(name):
    return _load(name)["mandate"]


def test_L1_create_then_execute_no_approval():
    engine = MandateEngine()
    created = engine.create_mandate(_body("valid-minimal.json"))
    assert created["status"] == "created"
    result = engine.execute_mandate(created["mandate_id"])
    assert result["status"] == "executed"
    with pytest.raises(MandateEngineError) as excinfo:
        engine.execute_mandate(created["mandate_id"])
    assert excinfo.value.code == errors.INVALID_TRANSITION


def test_L2_approval_gates_execution():
    engine = MandateEngine()
    created = engine.create_mandate(_body("valid-full.json"))
    assert created["status"] == "pending_approval"
    with pytest.raises(MandateEngineError) as excinfo:
        engine.execute_mandate(created["mandate_id"])
    assert excinfo.value.code == errors.APPROVAL_REQUIRED

    decided = engine.record_decision(created["mandate_id"], "did:ex:carol", "approve")
    assert decided["status"] == "pending_approval"
    with pytest.raises(MandateEngineError) as excinfo:
        engine.execute_mandate(created["mandate_id"])
    assert excinfo.value.code == errors.APPROVAL_REQUIRED

    decided = engine.record_decision(created["mandate_id"], "did:ex:dave", "approve")
    assert decided["status"] == "approved"
    assert engine.execute_mandate(created["mandate_id"])["status"] == "executed"


def test_L3_unauthorized_approver():
    engine = MandateEngine()
    created = engine.create_mandate(_body("valid-full.json"))
    for decision in ("approve", "reject"):
        with pytest.raises(MandateEngineError) as excinfo:
            engine.record_decision(created["mandate_id"], "did:ex:mallory", decision)
        assert excinfo.value.code == errors.UNAUTHORIZED_APPROVER
    assert engine.get_state(created["mandate_id"]) == "pending_approval"


def test_L4_single_rejection_rejects():
    engine = MandateEngine()
    created = engine.create_mandate(_body("valid-full.json"))
    engine.record_decision(created["mandate_id"], "did:ex:carol", "approve")
    decided = engine.record_decision(created["mandate_id"], "did:ex:dave", "reject")
    assert decided["status"] == "rejected"
    with pytest.raises(MandateEngineError) as excinfo:
        engine.execute_mandate(created["mandate_id"])
    assert excinfo.value.code == errors.MANDATE_REJECTED
    with pytest.raises(MandateEngineError) as excinfo:
        engine.record_decision(created["mandate_id"], "did:ex:carol", "approve")
    assert excinfo.value.code == errors.INVALID_TRANSITION


def test_L5_decision_change_while_pending():
    engine = MandateEngine()
    created = engine.create_mandate(_body("valid-full.json"))
    engine.record_decision(created["mandate_id"], "did:ex:carol", "approve")
    decided = engine.record_decision(created["mandate_id"], "did:ex:carol", "reject")
    assert decided["status"] == "rejected"
    event_types = [e["entry_type"] for e in engine.get_audit(created["mandate_id"])]
    assert "approval_recorded" in event_types
    assert "rejection_recorded" in event_types


def test_L6_idempotent_create_and_nonce_conflict():
    engine = MandateEngine()
    body = _body("valid-full.json")
    first = engine.create_mandate(body)
    second = engine.create_mandate(body)
    assert second["mandate_id"] == first["mandate_id"]
    created_events = [
        e for e in engine.get_audit(first["mandate_id"]) if e["entry_type"] == "mandate_created"
    ]
    assert len(created_events) == 1

    conflicting = dict(body, amount=999)
    with pytest.raises(MandateEngineError) as excinfo:
        engine.create_mandate(conflicting)
    assert excinfo.value.code == errors.NONCE_CONFLICT


def test_L7_expired_mandate_cannot_execute():
    engine = MandateEngine()
    body = {
        "issuer": "did:ex:alice",
        "beneficiary": "did:ex:bob",
        "expires_at": "2000-01-01T00:00:00Z",
        "intent": {
            "goal": "g",
            "expected_outcome": "o",
            "contextual_tone": "formal",
            "statistical_purpose": "s",
        },
    }
    created = engine.create_mandate(body)
    with pytest.raises(MandateEngineError) as excinfo:
        engine.execute_mandate(created["mandate_id"])
    assert excinfo.value.code == errors.MANDATE_EXPIRED
    assert engine.get_mandate(created["mandate_id"])["mandate_id"] == created["mandate_id"]


def test_L8_unknown_mandate():
    engine = MandateEngine()
    with pytest.raises(MandateEngineError) as excinfo:
        engine.get_mandate("no-such-mandate")
    assert excinfo.value.code == errors.NOT_FOUND
    with pytest.raises(MandateEngineError) as excinfo:
        engine.execute_mandate("no-such-mandate")
    assert excinfo.value.code == errors.NOT_FOUND


# ----------------------------------------------------------------------
# Audit + persistence requirements (spec sections 10 and 12)
# ----------------------------------------------------------------------

def test_audit_trail_events_and_shape():
    engine = MandateEngine()
    created = engine.create_mandate(_body("valid-full.json"))
    engine.record_decision(created["mandate_id"], "did:ex:carol", "approve")
    engine.record_decision(created["mandate_id"], "did:ex:dave", "approve")
    engine.execute_mandate(created["mandate_id"])
    audit = engine.get_audit(created["mandate_id"])
    types = [e["entry_type"] for e in audit]
    for expected in (
        "mandate_created",
        "gate_created",
        "approval_recorded",
        "gate_approved",
        "mandate_executed",
    ):
        assert expected in types, types
    for entry in audit:
        assert entry["mandate_id"] == created["mandate_id"]
        assert "timestamp" in entry
    executed = [e for e in audit if e["entry_type"] == "mandate_executed"][0]
    assert executed["payload"]["result"]["mock"] is True


def test_sqlite_store_survives_restart(tmp_path):
    db = tmp_path / "e4a.db"
    engine1 = MandateEngine(store=SQLiteStore(db))
    created = engine1.create_mandate(_body("valid-full.json"))
    engine1.record_decision(created["mandate_id"], "did:ex:carol", "approve")

    engine2 = MandateEngine(store=SQLiteStore(db))
    fetched = engine2.get_mandate(created["mandate_id"])
    assert fetched["status"] == "pending_approval"
    decided = engine2.record_decision(created["mandate_id"], "did:ex:dave", "approve")
    assert decided["status"] == "approved"
    assert engine2.execute_mandate(created["mandate_id"])["status"] == "executed"
    assert len(engine2.get_audit(created["mandate_id"])) >= 4


def test_adapter_uses_canonical_validation():
    """The A2A adapter must accept a canonical mandate and reject a v1-shaped one."""
    from adapters.a2a.adapter import E4A_A2A_Adapter

    adapter = E4A_A2A_Adapter()
    ok = adapter.create_mandate(_body("valid-minimal.json"))
    assert ok["status"] == "created"
    with pytest.raises(MandateEngineError) as excinfo:
        adapter.create_mandate(_load("invalid-missing-intent.json")["mandate"])
    assert excinfo.value.code == errors.VALIDATION_FAILED
