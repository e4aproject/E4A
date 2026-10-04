# sdk/python/e4a_sdk/mandate_engine.py
import json
import os
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path

from jsonschema import ValidationError, validate

from .gate_engine import GateEngine, GateEngineError

SPEC = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'specs', 'mandate_v2.json')

with open(SPEC, 'r') as _f:
    MANDATE_SCHEMA = json.load(_f)


class MandateEngineError(Exception):
    pass


class MandateEngine:
    def __init__(self, scribe=None, db_path: str | None = None):
        global MANDATE_SCHEMA
        with open(SPEC, 'r') as _f:
            MANDATE_SCHEMA = json.load(_f)

        base_dir = Path(__file__).resolve().parent.parent / "data"
        base_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = Path(db_path) if db_path else base_dir / "e4a_state.db"
        self.mandates = {}
        self.scribe = scribe
        self.gate_engine = GateEngine(db_path=str(self.db_path))
        self._init_db()
        self._load_mandates()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS mandates (mandate_id TEXT PRIMARY KEY, payload TEXT NOT NULL)"
            )

    def _load_mandates(self):
        with self._connect() as conn:
            rows = conn.execute("SELECT mandate_id, payload FROM mandates").fetchall()
        for row in rows:
            self.mandates[row["mandate_id"]] = json.loads(row["payload"])

    def _save_mandate(self, mandate):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO mandates (mandate_id, payload) VALUES (?, ?)",
                (mandate["mandate_id"], json.dumps(mandate, default=str)),
            )

    def validate_mandate(self, mandate):
        try:
            validate(instance=mandate, schema=MANDATE_SCHEMA)
        except ValidationError as e:
            raise MandateEngineError(f"Mandate validation error: {e.message}")

    def create_mandate(self, mandate):
        mandate = dict(mandate)
        if not mandate.get('mandate_id'):
            mandate['mandate_id'] = str(uuid.uuid4())
        mandate.setdefault('created_at', datetime.now(UTC).isoformat().replace('+00:00', 'Z'))
        self.validate_mandate(mandate)

        replay = mandate.get('replay_nonce')
        if replay:
            for m in self.mandates.values():
                if m.get('replay_nonce') == replay:
                    return m

        self.mandates[mandate['mandate_id']] = mandate
        self._save_mandate(mandate)

        if self.scribe:
            self.scribe.append_entry({
                'entry_type': 'mandate_created',
                'mandate_id': mandate['mandate_id'],
                'payload': mandate,
            })
        return mandate

    def create_submandate(self, parent_id, subpayload):
        parent = self.mandates.get(parent_id)
        if not parent:
            raise MandateEngineError('Parent mandate not found')

        sub = dict(subpayload)
        sub.setdefault('parent_mandate_id', parent_id)

        if parent.get('inherit_values'):
            sub.setdefault('policy_tags', parent.get('policy_tags', []))
            sub.setdefault('fee_distribution', parent.get('fee_distribution', {}))

        return self.create_mandate(sub)

    def process_fees(self, mandate_id):
        mandate = self.mandates.get(mandate_id)
        if not mandate:
            raise MandateEngineError('Mandate not found for fee processing')
        total = mandate.get('amount', 0.0)
        fees = mandate.get('fee_distribution', {})
        protocol_share = fees.get('protocol', 0.0)
        validator_share = fees.get('validator', 0.0)
        issuer_share = fees.get('issuer', 0.0)
        return {
            'protocol_amount': protocol_share * total,
            'validator_amount': validator_share * total,
            'issuer_amount': issuer_share * total,
        }

    def execute_mandate(self, mandate_id, executor_id='system'):
        mandate = self.mandates.get(mandate_id)
        if not mandate:
            self._load_mandates()
            mandate = self.mandates.get(mandate_id)
        if not mandate:
            raise MandateEngineError('Mandate not found')

        required_approvers = mandate.get('intent', {}).get('requires_approval', [])
        if required_approvers:
            gate = self.gate_engine.get_gate_by_mandate_id(mandate_id)
            if gate:
                if gate['status'] == 'pending':
                    raise MandateEngineError(f"Mandate {mandate_id} requires human approval and is pending. Gate ID: {gate['gate_id']}")
                if gate['status'] == 'rejected':
                    raise MandateEngineError(f"Mandate {mandate_id} was rejected by human approvers. Gate ID: {gate['gate_id']}")
            else:
                gate = self.gate_engine.create_gate(mandate_id, required_approvers, mandate)
                raise MandateEngineError(f"Mandate {mandate_id} requires human approval. A new gate (ID: {gate['gate_id']}) has been created and is pending.")

        result = {
            'status': 'executed',
            'executor': executor_id,
            'executed_at': datetime.now(UTC).isoformat().replace('+00:00', 'Z'),
        }
        result['fees'] = self.process_fees(mandate_id)

        if self.scribe:
            self.scribe.append_entry({
                'entry_type': 'mandate_executed',
                'mandate_id': mandate_id,
                'executor': executor_id,
                'result': result,
            })
        return result


if __name__ == '__main__':
    from sdk.python.e4a_sdk.scribe_agent import ScribeAgent

    scribe = ScribeAgent()
    engine = MandateEngine(scribe=scribe)

    sample_approved = {
        'issuer': 'did:example:alice',
        'beneficiary': 'did:example:bob',
        'amount': 100.0,
        'currency': 'USD',
        'fee_distribution': {'protocol': 0.01, 'validator': 0.01, 'issuer': 0.01},
        'intent': {
            'goal': 'transfer funds',
            'expected_outcome': 'funds transferred',
            'contextual_tone': 'formal',
            'statistical_purpose': 'facilitate transaction',
        },
    }

    sample_requires_approval = {
        'issuer': 'did:example:charlie',
        'beneficiary': 'did:example:diana',
        'amount': 1000.0,
        'currency': 'USD',
        'fee_distribution': {'protocol': 0.01, 'validator': 0.01, 'issuer': 0.01},
        'intent': {
            'goal': 'deploy critical system',
            'expected_outcome': 'system deployed',
            'contextual_tone': 'urgent',
            'statistical_purpose': 'ensure operational continuity',
            'requires_approval': ['human-admin', 'human-security'],
        },
    }

    print("\n--- Testing Mandate without Approval ---")
    m_approved = engine.create_mandate(sample_approved)
    print('Created mandate:', m_approved['mandate_id'])
    try:
        print('Execute result:', engine.execute_mandate(m_approved['mandate_id']))
    except MandateEngineError as e:
        print(f"Execution failed: {e}")

    print("\n--- Testing Mandate Requiring Approval ---")
    m_pending = engine.create_mandate(sample_requires_approval)
    print('Created mandate:', m_pending['mandate_id'])
    try:
        print('Execute result:', engine.execute_mandate(m_pending['mandate_id']))
    except MandateEngineError as e:
        print(f"Execution failed: {e}")

    print("\n--- Approving the pending mandate ---")
    try:
        gate_id = None
        try:
            gate_id = engine.gate_engine.get_gate_status(m_pending['mandate_id'])['gate_id']
        except GateEngineError:
            pass

        try:
            engine.execute_mandate(m_pending['mandate_id'])
        except MandateEngineError as e:
            import re
            match = re.search(r'Gate ID: ([a-f0-9-]+)', str(e))
            if match:
                gate_id = match.group(1)
                print(f"Extracted Gate ID: {gate_id}")

        if gate_id:
            engine.gate_engine.approve_gate(gate_id, 'human-admin')
            engine.gate_engine.approve_gate(gate_id, 'human-security')
            print('Gate status after approval:', engine.gate_engine.get_gate_status(gate_id))
            print('Execute result after approval:', engine.execute_mandate(m_pending['mandate_id']))
    except MandateEngineError as e:
        print(f"Execution failed after approval attempt: {e}")

__all__ = ["MandateEngine", "MandateEngineError"]




































































































































































\n

























































































































































n















































"}]}  ,