import json
import os
import sqlite3
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from jsonschema import ValidationError, validate

SPEC = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'specs', 'gate_v1.json')

with open(SPEC, 'r', encoding='utf-8') as _f:
    GATE_SCHEMA = json.load(_f)


class GateEngineError(Exception):
    pass


class GateEngine:
    def __init__(self, db_path: str | None = None):
        base_dir = Path(__file__).resolve().parent.parent / "data"
        base_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = Path(db_path) if db_path else base_dir / "e4a_state.db"
        self.gates = {}
        self._init_db()
        self._load_gates()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS gates (gate_id TEXT PRIMARY KEY, payload TEXT NOT NULL)"
            )

    def _load_gates(self):
        with self._connect() as conn:
            rows = conn.execute("SELECT gate_id, payload FROM gates").fetchall()
        for row in rows:
            self.gates[row["gate_id"]] = json.loads(row["payload"])

    def _save_gate(self, gate: dict):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO gates (gate_id, payload) VALUES (?, ?)",
                (gate["gate_id"], json.dumps(gate, default=str)),
            )

    def _validate_gate(self, gate):
        try:
            validate(instance=gate, schema=GATE_SCHEMA)
        except ValidationError as e:
            raise GateEngineError(f"Gate validation error: {e.message}") from e

    def create_gate(self, mandate_id: str, required_approvers: list[str], payload: dict, expires_in_seconds: int = None) -> dict:
        gate_id = str(uuid.uuid4())
        created_at = datetime.now(UTC).isoformat().replace('+00:00', 'Z')
        expires_at = None
        if expires_in_seconds:
            expires_at = (datetime.now(UTC) + timedelta(seconds=expires_in_seconds)).isoformat().replace('+00:00', 'Z')

        gate = {
            'gate_id': gate_id,
            'mandate_id': mandate_id,
            'status': 'pending',
            'required_approvers': required_approvers,
            'approvals': [],
            'rejections': [],
            'created_at': created_at,
            'expires_at': expires_at,
            'payload': payload,
        }
        self._validate_gate(gate)
        self.gates[gate_id] = gate
        self._save_gate(gate)
        return gate

    def get_gate_status(self, gate_id: str) -> dict:
        gate = self.gates.get(gate_id)
        if gate is None:
            self._load_gates()
            gate = self.gates.get(gate_id)
        if gate is None:
            raise GateEngineError('Gate not found')
        return gate

    def get_gate_by_mandate_id(self, mandate_id: str) -> dict | None:
        self._load_gates()
        for gate in self.gates.values():
            if gate['mandate_id'] == mandate_id:
                return gate
        return None

    def _check_resolution(self, gate_id: str):
        gate = self.gates[gate_id]
        if gate['status'] != 'pending':
            return

        if gate['expires_at']:
            expires_dt = datetime.fromisoformat(gate['expires_at'].replace('Z', ''))
            if datetime.now(UTC).replace(tzinfo=None) > expires_dt:
                gate['status'] = 'rejected'
                self._save_gate(gate)
                return

        approved_count = len(set(gate['required_approvers']) & set(gate['approvals']))
        if approved_count >= len(gate['required_approvers']):
            gate['status'] = 'approved'
            self._save_gate(gate)
            return

        if any(approver in gate['rejections'] for approver in gate['required_approvers']):
            gate['status'] = 'rejected'
            self._save_gate(gate)
            return

    def approve_gate(self, gate_id: str, approver_id: str) -> dict:
        gate = self.get_gate_status(gate_id)
        if gate['status'] != 'pending':
            raise GateEngineError(f"Gate {gate_id} is already {gate['status']}")
        if approver_id not in gate['required_approvers']:
            raise GateEngineError(f'Approver {approver_id} is not authorized for gate {gate_id}')

        if approver_id not in gate['approvals']:
            gate['approvals'].append(approver_id)
        if approver_id in gate['rejections']:
            gate['rejections'].remove(approver_id)

        self._check_resolution(gate_id)
        self._save_gate(gate)
        return gate

    def reject_gate(self, gate_id: str, rejector_id: str) -> dict:
        gate = self.get_gate_status(gate_id)
        if gate['status'] != 'pending':
            raise GateEngineError(f"Gate {gate_id} is already {gate['status']}")
        if rejector_id not in gate['required_approvers']:
            raise GateEngineError(f'Rejector {rejector_id} is not authorized for gate {gate_id}')

        if rejector_id not in gate['rejections']:
            gate['rejections'].append(rejector_id)
        if rejector_id in gate['approvals']:
            gate['approvals'].remove(rejector_id)

        self._check_resolution(gate_id)
        self._save_gate(gate)
        return gate


if __name__ == '__main__':
    engine = GateEngine()
    gate = engine.create_gate('mandate-123', ['human-alice', 'human-bob'], {'action': 'deploy_critical_system'}, expires_in_seconds=60)
    print('Created Gate:', gate)

    print('Approving with Alice...')
    engine.approve_gate(gate['gate_id'], 'human-alice')
    print('Gate Status:', engine.get_gate_status(gate['gate_id']))

    print('Approving with Bob...')
    engine.approve_gate(gate['gate_id'], 'human-bob')
    print('Gate Status:', engine.get_gate_status(gate['gate_id']))

    gate2 = engine.create_gate('mandate-456', ['human-charlie'], {'action': 'delete_data'})
    print('Created Gate 2:', gate2)
    print('Rejecting with Charlie...')
    engine.reject_gate(gate2['gate_id'], 'human-charlie')
    print('Gate 2 Status:', engine.get_gate_status(gate2['gate_id']))
