"""
Gate Engine for E4A 1.0 approval gates (spec sections 4, 5, 8).

Semantics:
- A gate is created when a mandate requiring approval is submitted.
- Only listed required approvers may approve or reject.
- The gate resolves 'approved' when ALL required approvers have approved,
  'rejected' as soon as ANY required approver rejects, and 'expired' when
  its expiry passes — expiry is distinct from rejection (spec section 5).
- Decisions may be changed by the same actor while the gate is pending;
  a resolved gate is final.
- All failures are E4AError subclasses carrying stable protocol codes.
"""

import uuid
from datetime import datetime, timedelta, UTC

from jsonschema import validate, ValidationError

from . import errors
from .schema import GATE_SCHEMA


class GateEngineError(errors.E4AError):
    code = errors.VALIDATION_FAILED


def _now():
    return datetime.now(UTC)


def _iso(dt):
    return dt.isoformat().replace("+00:00", "Z")


class GateEngine:
    def __init__(self, store=None):
        self.store = store
        self.gates = {}
        if store is not None:
            # Rehydrate in-memory view from the persistent store, if it can list gates.
            loader = getattr(store, "all_gates", None)
            if callable(loader):
                for gate in loader():
                    self.gates[gate["gate_id"]] = gate

    # ------------------------------------------------------------------
    def _save(self, gate):
        self.gates[gate["gate_id"]] = gate
        if self.store is not None:
            self.store.put_gate(gate)

    def _validate_gate(self, gate):
        try:
            validate(instance=gate, schema=GATE_SCHEMA)
        except ValidationError as e:
            raise GateEngineError(f"Gate validation error: {e.message}", code=errors.VALIDATION_FAILED)

    # ------------------------------------------------------------------
    def create_gate(
        self,
        mandate_id: str,
        required_approvers: list,
        payload: dict,
        expires_in_seconds: int | None = None,
        expires_at: str | None = None,
    ) -> dict:
        created = _now()
        if expires_at is None and expires_in_seconds:
            expires_at = _iso(created + timedelta(seconds=expires_in_seconds))
        gate = {
            "gate_id": str(uuid.uuid4()),
            "mandate_id": mandate_id,
            "status": "pending",
            "required_approvers": list(required_approvers),
            "approvals": [],
            "rejections": [],
            "created_at": _iso(created),
            "expires_at": expires_at,
            "payload": payload,
        }
        self._validate_gate(gate)
        self._save(gate)
        return gate

    def get_gate_status(self, gate_id: str) -> dict:
        gate = self.gates.get(gate_id) or (self.store.get_gate(gate_id) if self.store else None)
        if not gate:
            raise GateEngineError("Gate not found", code=errors.NOT_FOUND)
        self.gates[gate_id] = gate
        self._check_resolution(gate_id)
        return self.gates[gate_id]

    def get_gate_by_mandate_id(self, mandate_id: str):
        for gate in self.gates.values():
            if gate["mandate_id"] == mandate_id:
                self._check_resolution(gate["gate_id"])
                return self.gates[gate["gate_id"]]
        if self.store is not None:
            gate = self.store.get_gate_by_mandate(mandate_id)
            if gate:
                self.gates[gate["gate_id"]] = gate
                self._check_resolution(gate["gate_id"])
                return self.gates[gate["gate_id"]]
        return None

    # ------------------------------------------------------------------
    def _is_expired(self, gate):
        if not gate.get("expires_at"):
            return False
        expires_dt = datetime.fromisoformat(gate["expires_at"].replace("Z", "+00:00"))
        return _now() > expires_dt

    def _check_resolution(self, gate_id: str):
        gate = self.gates[gate_id]
        if gate["status"] != "pending":
            return
        changed = False
        if self._is_expired(gate):
            gate["status"] = "expired"
            changed = True
        elif any(a in gate["rejections"] for a in gate["required_approvers"]):
            gate["status"] = "rejected"
            changed = True
        elif len(gate["required_approvers"]) > 0 and all(a in gate["approvals"] for a in gate["required_approvers"]):
            gate["status"] = "approved"
            changed = True
        if changed:
            self._save(gate)

    # ------------------------------------------------------------------
    def _decide(self, gate_id: str, actor: str, decision: str) -> dict:
        gate = self.gates.get(gate_id) or (self.store.get_gate(gate_id) if self.store else None)
        if not gate:
            raise GateEngineError("Gate not found", code=errors.NOT_FOUND)
        self.gates[gate_id] = gate
        self._check_resolution(gate_id)
        gate = self.gates[gate_id]
        if gate["status"] != "pending":
            raise GateEngineError(f"Gate {gate_id} is already {gate['status']}", code=errors.INVALID_TRANSITION)
        if actor not in gate["required_approvers"]:
            role = "Approver" if decision == "approve" else "Rejector"
            raise GateEngineError(
                f"{role} {actor} is not authorized for gate {gate_id}",
                code=errors.UNAUTHORIZED_APPROVER,
            )
        if decision == "approve":
            if actor in gate["rejections"]:
                gate["rejections"].remove(actor)
            if actor not in gate["approvals"]:
                gate["approvals"].append(actor)
        else:
            if actor in gate["approvals"]:
                gate["approvals"].remove(actor)
            if actor not in gate["rejections"]:
                gate["rejections"].append(actor)
        self._save(gate)
        self._check_resolution(gate_id)
        return self.gates[gate_id]

    def approve_gate(self, gate_id: str, approver_id: str) -> dict:
        return self._decide(gate_id, approver_id, "approve")

    def reject_gate(self, gate_id: str, rejector_id: str) -> dict:
        return self._decide(gate_id, rejector_id, "reject")
