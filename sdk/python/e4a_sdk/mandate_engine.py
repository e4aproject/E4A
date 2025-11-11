"""
Minimal Mandate Engine (Phase 1 reference implementation).

Responsibilities:
- validate mandate payloads against spec (JSON Schema)
- create mandates and sub-mandates (idempotent via replay_nonce when provided)
- execute mandates by calling adapters (mocked)
- compute protocol/validator/issuer fee splits
"""

import json
import os
import uuid
from datetime import datetime, UTC
from jsonschema import validate, ValidationError
from .gate_engine import GateEngine, GateEngineError

SPEC = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'specs', 'mandate_v2.json')

with open(SPEC, 'r') as _f:
    MANDATE_SCHEMA = json.load(_f)


class MandateEngineError(Exception):
    pass


class MandateEngine:
    def __init__(self, scribe=None):
        # Reload schema to ensure latest version is always used in tests
        global MANDATE_SCHEMA
        with open(SPEC, 'r') as _f:
            MANDATE_SCHEMA = json.load(_f)

        # in-memory store for Phase 1 (replace with persistence later)
        self.mandates = {}
        self.scribe = scribe
        self.gate_engine = GateEngine()

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

        # validate
        self.validate_mandate(mandate)

        # idempotency via replay_nonce (phase 1: simple scan)
        replay = mandate.get('replay_nonce')
        if replay:
            for m in self.mandates.values():
                if m.get('replay_nonce') == replay:
                    return m

        self.mandates[mandate['mandate_id']] = mandate

        if self.scribe:
            self.scribe.append_entry({
                'entry_type': 'mandate_created',
                'mandate_id': mandate['mandate_id'],
                'payload': mandate
            })
        return mandate

    def create_submandate(self, parent_id, subpayload):
        parent = self.mandates.get(parent_id)
        if not parent:
            raise MandateEngineError('Parent mandate not found')

        sub = dict(subpayload)
        sub.setdefault('parent_mandate_id', parent_id)

        # conditional inheritance: copy certain fields if parent requests it
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
            'issuer_amount': issuer_share * total
        }

    def execute_mandate(self, mandate_id, executor_id='system'):
        mandate = self.mandates.get(mandate_id)
        if not mandate:
            raise MandateEngineError('Mandate not found')

        # Check for human approval if required
        required_approvers = mandate.get('intent', {}).get('requires_approval', [])
        if required_approvers:
            gate = self.gate_engine.get_gate_by_mandate_id(mandate_id)
            if gate:
                if gate['status'] == 'pending':
                    raise MandateEngineError(f"Mandate {mandate_id} requires human approval and is pending. Gate ID: {gate['gate_id']}")
                elif gate['status'] == 'rejected':
                    raise MandateEngineError(f"Mandate {mandate_id} was rejected by human approvers. Gate ID: {gate['gate_id']}")
                # If approved, proceed
            else: # Gate not found, create it
                gate = self.gate_engine.create_gate(mandate_id, required_approvers, mandate)
                raise MandateEngineError(f"Mandate {mandate_id} requires human approval. A new gate (ID: {gate['gate_id']}) has been created and is pending.")

        # Phase 1: mock execution — record action and compute fees
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
                'result': result
            })
        return result


if __name__ == '__main__':
    # simple demo run if executed directly
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
            'statistical_purpose': 'facilitate transaction'
        }
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
            'requires_approval': ['human-admin', 'human-security']
        }
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
        # Assuming 'human-admin' approves it
        gate_id = None
        try:
            gate_id = engine.gate_engine.get_gate_status(m_pending['mandate_id'])['gate_id']
        except GateEngineError:
            # This might happen if the gate was just created and not yet retrieved by ID
            pass # We'll rely on the error message from execute_mandate to get the gate_id

        # This part is a bit hacky for the demo, in a real system, the gate_id would be known
        # from the error message or a separate API call.
        # For now, let's assume the gate_id is the same as mandate_id for simplicity in this demo block
        # In the actual GateEngine, gate_id is distinct. We need to retrieve it.
        # Let's re-run the execute_mandate to get the error with the gate_id
        try:
            engine.execute_mandate(m_pending['mandate_id'])
        except MandateEngineError as e:
            import re
            match = re.search(r'Gate ID: ([a-f0-9-]+)', str(e))
            if match:
                gate_id = match.group(1)
                print(f"Extracted Gate ID: {gate_id}")
            else:
                print("Could not extract Gate ID from error message.")

        if gate_id:
            engine.gate_engine.approve_gate(gate_id, 'human-admin')
            engine.gate_engine.approve_gate(gate_id, 'human-security')
            print('Gate status after approval:', engine.gate_engine.get_gate_status(gate_id))
            print('Execute result after approval:', engine.execute_mandate(m_pending['mandate_id']))
    except MandateEngineError as e:
        print(f"Execution failed after approval attempt: {e}")
