"""Spec section 10 conformance: audit records.

For a full gated lifecycle, the audit trail retrievable by mandate_id MUST
contain the section 4 events in order, each record MUST carry entry_type,
mandate_id, and an RFC 3339 timestamp, the section 10 required payload
fields MUST be present, and mandate_executed MUST be marked mock: true.
"""

from conftest import state_of, vector_mandate

REQUIRED_EVENTS = [
    "mandate_created",
    "gate_created",
    "approval_recorded",
    "gate_approved",
    "mandate_executed",
]


def _payload(record):
    return record.get("payload") or {}


def test_audit_trail_for_gated_lifecycle(engine):
    mandate = vector_mandate("valid-full.json")
    mandate.pop("mandate_id", None)
    created = engine.create_mandate(mandate)
    mandate_id = created["mandate_id"]
    engine.record_decision(mandate_id, "did:ex:carol", "approve")
    engine.record_decision(mandate_id, "did:ex:dave", "approve")
    result = engine.execute_mandate(mandate_id)
    assert state_of(result) == "executed"

    audit = engine.get_audit(mandate_id)
    assert isinstance(audit, list) and audit, "audit trail must be retrievable by mandate_id"

    for record in audit:
        assert record.get("entry_type"), "every audit record carries entry_type"
        assert record.get("mandate_id") == mandate_id
        timestamp = record.get("timestamp")
        assert timestamp and "T" in timestamp, "every audit record carries an RFC 3339 timestamp"

    event_types = [r["entry_type"] for r in audit]
    positions = [event_types.index(name) for name in REQUIRED_EVENTS]
    assert positions == sorted(positions), f"lifecycle events out of order: {event_types}"

    by_type = {}
    for record in audit:
        by_type.setdefault(record["entry_type"], record)

    gate_created = _payload(by_type["gate_created"])
    assert gate_created.get("gate_id")
    assert set(gate_created.get("required_approvers") or []) == {"did:ex:carol", "did:ex:dave"}

    approval = _payload(by_type["approval_recorded"])
    assert approval.get("gate_id") and approval.get("actor")

    executed = _payload(by_type["mandate_executed"])
    assert executed.get("mock") is True, "mock execution MUST be marked mock: true (spec 7/10)"
