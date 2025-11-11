import json
import os
import uuid
from datetime import datetime, timedelta, UTC
from jsonschema import validate, ValidationError

SPEC = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'specs', 'gate_v1.json')

with open(SPEC, 'r') as _f:
    GATE_SCHEMA = json.load(_f)


class GateEngineError(Exception):
    pass


class GateEngine:
    def __init__(self):
        self.gates = {}

    def _validate_gate(self, gate):
        try:
            validate(instance=gate, schema=GATE_SCHEMA)
        except ValidationError as e:
            raise GateEngineError(f"Gate validation error: {e.message}")

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
            'payload': payload
        }
        self._validate_gate(gate)
        self.gates[gate_id] = gate
        return gate

    def get_gate_status(self, gate_id: str) -> dict:
        gate = self.gates.get(gate_id)
        if not gate:
            raise GateEngineError('Gate not found')
        return gate

    def get_gate_by_mandate_id(self, mandate_id: str) -> dict | None:
        for gate in self.gates.values():
            if gate['mandate_id'] == mandate_id:
                return gate
        return None

    def _check_resolution(self, gate_id: str):
        gate = self.gates[gate_id]
        if gate['status'] != 'pending':
            return

        # Check for expiration
        if gate['expires_at']:
            expires_dt = datetime.fromisoformat(gate['expires_at'].replace('Z', ''))
            if datetime.now(UTC).replace(tzinfo=None) > expires_dt:
                gate['status'] = 'rejected' # Or 'expired'
                return

        # Check for approval
        approved_count = len(set(gate['required_approvers']) & set(gate['approvals']))
        if approved_count >= len(gate['required_approvers']):
            gate['status'] = 'approved'
            return

        # Check for rejection (if any required approver rejects, it's rejected)
        if any(approver in gate['rejections'] for approver in gate['required_approvers']):
            gate['status'] = 'rejected'
            return

    def approve_gate(self, gate_id: str, approver_id: str) -> dict:
        gate = self.gates.get(gate_id)
        if not gate:
            raise GateEngineError('Gate not found')
        if gate['status'] != 'pending':
            raise GateEngineError(f'Gate {gate_id} is already {gate['status']}')
        if approver_id not in gate['required_approvers']:
            raise GateEngineError(f'Approver {approver_id} is not authorized for gate {gate_id}')

        if approver_id not in gate['approvals']:
            gate['approvals'].append(approver_id)
        
        # Remove from rejections if previously rejected
        if approver_id in gate['rejections']:
            gate['rejections'].remove(approver_id)

        self._check_resolution(gate_id)
        return gate

    def reject_gate(self, gate_id: str, rejector_id: str) -> dict:
        gate = self.gates.get(gate_id)
        if not gate:
            raise GateEngineError('Gate not found')
        if gate['status'] != 'pending':
            raise GateEngineError(f'Gate {gate_id} is already {gate['status']}')
        if rejector_id not in gate['required_approvers']:
            raise GateEngineError(f'Rejector {rejector_id} is not authorized for gate {gate_id}')

        if rejector_id not in gate['rejections']:
            gate['rejections'].append(rejector_id)

        # Remove from approvals if previously approved
        if rejector_id in gate['approvals']:
            gate['approvals'].remove(rejector_id)

        self._check_resolution(gate_id)
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