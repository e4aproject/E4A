"""
Mandate Engine — E4A 1.0 reference implementation of the protocol lifecycle
(see docs/protocol/spec.md).

Implements:
- validation against the single canonical schema bundled in the package
  (e4a_sdk.schema.MANDATE_SCHEMA) — one validation path for all callers
- the explicit lifecycle state machine (spec section 4):
  created / pending_approval / approved / executed / rejected / expired / failed
- approval gates created at submission time (spec sections 4, 8)
- idempotency per (issuer, replay_nonce) with conflict detection (section 6)
- expiry for mandates and gates, distinct from rejection (section 5)
- mock execution, unmistakably marked (section 7)
- audit records for every lifecycle event (section 10)
- persistence through a store interface (section 12): in-memory by default,
  SQLite for the reference deployment

All protocol failures raise MandateEngineError (an E4AError) carrying a
stable ``code`` from e4a_sdk.errors. Branch on the code, not the message.
"""

import copy
import uuid
from datetime import datetime, UTC

from jsonschema import validate, ValidationError

from . import errors
from .gate_engine import GateEngine, GateEngineError
from .schema import MANDATE_SCHEMA, PROTOCOL_VERSION
from .store import InMemoryStore

TERMINAL_STATES = {"executed", "rejected", "expired", "failed"}


class MandateEngineError(errors.E4AError):
    code = errors.VALIDATION_FAILED


def _now_iso():
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _parse_ts(value):
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class MandateEngine:
    def __init__(self, scribe=None, store=None, gate_engine=None):
        self.store = store if store is not None else InMemoryStore()
        self.scribe = scribe
        self.gate_engine = gate_engine if gate_engine is not None else GateEngine(store=self.store)
        # Backwards-compatible view used by older callers/tests.
        self.mandates = {}

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------
    def _audit(self, entry_type, mandate_id, payload):
        record = {"entry_type": entry_type, "mandate_id": mandate_id, "payload": payload}
        self.store.append_audit(mandate_id, dict(record, timestamp=_now_iso()))
        if self.scribe:
            self.scribe.append_entry(record)

    def _record(self, mandate_id):
        record = self.store.get_mandate(mandate_id)
        if record is None:
            raise MandateEngineError(f"Mandate {mandate_id} not found", code=errors.NOT_FOUND)
        return record

    def _public(self, record):
        out = copy.deepcopy(record["mandate"])
        out["status"] = record["state"]
        return out

    def _sync_view(self, record):
        self.mandates[record["mandate"]["mandate_id"]] = self._public(record)

    def _refresh_state(self, record):
        """Apply time- and gate-driven transitions (expiry, gate resolution)."""
        state = record["state"]
        mandate = record["mandate"]
        if state in TERMINAL_STATES:
            return record
        # Mandate-level expiry
        expires_at = _parse_ts(mandate.get("expires_at"))
        if expires_at and datetime.now(UTC) > expires_at and state in ("created", "approved", "pending_approval"):
            record["state"] = "expired"
            self.store.put_mandate(record)
            self._sync_view(record)
            return record
        if state == "pending_approval":
            gate = self.gate_engine.get_gate_by_mandate_id(mandate["mandate_id"])
            if gate:
                if gate["status"] == "approved" and record["state"] != "approved":
                    record["state"] = "approved"
                    self.store.put_mandate(record)
                    self._audit(
                        "gate_approved",
                        mandate["mandate_id"],
                        {"gate_id": gate["gate_id"], "approvals": gate["approvals"]},
                    )
                elif gate["status"] == "rejected" and record["state"] != "rejected":
                    record["state"] = "rejected"
                    self.store.put_mandate(record)
                    self._audit(
                        "gate_rejected",
                        mandate["mandate_id"],
                        {"gate_id": gate["gate_id"], "rejections": gate["rejections"]},
                    )
                elif gate["status"] == "expired" and record["state"] != "expired":
                    record["state"] = "expired"
                    self.store.put_mandate(record)
                    self._audit("gate_expired", mandate["mandate_id"], {"gate_id": gate["gate_id"]})
                self._sync_view(record)
        return record

    # ------------------------------------------------------------------
    # validation
    # ------------------------------------------------------------------
    def validate_mandate(self, mandate):
        version = mandate.get("protocol_version", PROTOCOL_VERSION)
        if version != PROTOCOL_VERSION:
            raise MandateEngineError(f"Unsupported protocol_version: {version!r}", code=errors.UNSUPPORTED_VERSION)
        try:
            validate(instance=mandate, schema=MANDATE_SCHEMA)
        except ValidationError as e:
            raise MandateEngineError(f"Mandate validation error: {e.message}", code=errors.VALIDATION_FAILED)

    # ------------------------------------------------------------------
    # lifecycle
    # ------------------------------------------------------------------
    def create_mandate(self, mandate):
        submission = copy.deepcopy(mandate)

        # Idempotency (spec section 6): (issuer, replay_nonce) is unique.
        nonce = submission.get("replay_nonce")
        issuer = submission.get("issuer")
        if nonce and issuer:
            existing = self.store.find_by_nonce(issuer, nonce)
            if existing is not None:
                if existing.get("submission") == submission:
                    return self._public(self._refresh_state(existing))
                raise MandateEngineError(
                    f"replay_nonce {nonce!r} already used by issuer {issuer!r} with a different mandate",
                    code=errors.NONCE_CONFLICT,
                )

        mandate = copy.deepcopy(submission)
        if not mandate.get("mandate_id"):
            mandate["mandate_id"] = str(uuid.uuid4())
        mandate.setdefault("protocol_version", PROTOCOL_VERSION)
        mandate.setdefault("created_at", _now_iso())

        self.validate_mandate(mandate)

        required_approvers = mandate.get("intent", {}).get("requires_approval") or []
        state = "pending_approval" if required_approvers else "created"
        record = {"mandate": mandate, "state": state, "submission": submission}
        self.store.put_mandate(record)
        self._sync_view(record)
        self._audit("mandate_created", mandate["mandate_id"], {"mandate": mandate})

        if required_approvers:
            gate = self.gate_engine.create_gate(
                mandate["mandate_id"],
                required_approvers,
                mandate,
                expires_at=mandate.get("expires_at"),
            )
            self._audit(
                "gate_created",
                mandate["mandate_id"],
                {
                    "gate_id": gate["gate_id"],
                    "required_approvers": required_approvers,
                    "expires_at": gate["expires_at"],
                },
            )

        # A mandate whose expiry is already past is stored but expired.
        record = self._refresh_state(record)
        return self._public(record)

    def create_submandate(self, parent_id, subpayload):
        parent = self.store.get_mandate(parent_id)
        if parent is None:
            raise MandateEngineError("Parent mandate not found", code=errors.NOT_FOUND)
        parent_mandate = parent["mandate"]
        sub = dict(subpayload)
        sub.setdefault("parent_mandate_id", parent_id)
        if parent_mandate.get("inherit_values"):
            sub.setdefault("policy_tags", parent_mandate.get("policy_tags", []))
            sub.setdefault("fee_distribution", parent_mandate.get("fee_distribution", {}))
        return self.create_mandate(sub)

    def get_mandate(self, mandate_id):
        return self._public(self._refresh_state(self._record(mandate_id)))

    def get_state(self, mandate_id):
        return self._refresh_state(self._record(mandate_id))["state"]

    def get_audit(self, mandate_id):
        self._record(mandate_id)
        return self.store.get_audit(mandate_id)

    # ------------------------------------------------------------------
    # decisions
    # ------------------------------------------------------------------
    def record_decision(self, mandate_id, actor, decision):
        """Record an approve/reject decision from a required approver (spec section 8)."""
        record = self._refresh_state(self._record(mandate_id))
        if record["state"] != "pending_approval":
            raise MandateEngineError(
                f"Mandate {mandate_id} is not pending approval (state: {record['state']})",
                code=errors.INVALID_TRANSITION,
            )
        gate = self.gate_engine.get_gate_by_mandate_id(mandate_id)
        if gate is None:
            raise MandateEngineError(f"Mandate {mandate_id} has no approval gate", code=errors.NOT_FOUND)
        try:
            if decision == "approve":
                gate = self.gate_engine.approve_gate(gate["gate_id"], actor)
            elif decision == "reject":
                gate = self.gate_engine.reject_gate(gate["gate_id"], actor)
            else:
                raise MandateEngineError(
                    f"Invalid decision: {decision!r} (expected 'approve' or 'reject')",
                    code=errors.VALIDATION_FAILED,
                )
        except GateEngineError as e:
            # Surface gate failures through the engine's error type, keeping the code.
            raise MandateEngineError(str(e), code=e.code)
        event = "approval_recorded" if decision == "approve" else "rejection_recorded"
        self._audit(
            event,
            mandate_id,
            {
                "gate_id": gate["gate_id"],
                "actor": actor,
                "decision": decision,
                "approvals": gate["approvals"],
                "rejections": gate["rejections"],
            },
        )
        record = self._refresh_state(self._record(mandate_id))
        return self._public(record)

    # ------------------------------------------------------------------
    # fees (record-keeping; mock execution moves no value)
    # ------------------------------------------------------------------
    def process_fees(self, mandate_id):
        record = self.store.get_mandate(mandate_id)
        if record is None:
            raise MandateEngineError("Mandate not found for fee processing", code=errors.NOT_FOUND)
        mandate = record["mandate"]
        total = mandate.get("amount", 0.0)
        fees = mandate.get("fee_distribution", {})
        return {
            "protocol_amount": fees.get("protocol", 0.0) * total,
            "validator_amount": fees.get("validator", 0.0) * total,
            "issuer_amount": fees.get("issuer", 0.0) * total,
        }

    # ------------------------------------------------------------------
    # execution (mock — spec section 7)
    # ------------------------------------------------------------------
    def execute_mandate(self, mandate_id, executor_id="system"):
        record = self._refresh_state(self._record(mandate_id))
        state = record["state"]

        if state == "executed":
            raise MandateEngineError(f"Mandate {mandate_id} has already been executed", code=errors.INVALID_TRANSITION)
        if state == "rejected":
            raise MandateEngineError(
                f"Mandate {mandate_id} was rejected by human approvers", code=errors.MANDATE_REJECTED
            )
        if state == "expired":
            raise MandateEngineError(f"Mandate {mandate_id} has expired", code=errors.MANDATE_EXPIRED)
        if state == "failed":
            raise MandateEngineError(f"Mandate {mandate_id} is in state 'failed'", code=errors.INVALID_TRANSITION)
        if state == "pending_approval":
            gate = self.gate_engine.get_gate_by_mandate_id(mandate_id)
            gate_id = gate["gate_id"] if gate else None
            raise MandateEngineError(
                f"Mandate {mandate_id} requires human approval and is pending. Gate ID: {gate_id}",
                code=errors.APPROVAL_REQUIRED,
            )
        # state is 'created' or 'approved'
        result = {
            "status": "executed",
            "mock": True,
            "executor": executor_id,
            "executed_at": _now_iso(),
            "fees": self.process_fees(mandate_id),
        }
        record["state"] = "executed"
        self.store.put_mandate(record)
        self._sync_view(record)
        self._audit("mandate_executed", mandate_id, {"executor": executor_id, "result": result})
        return result
