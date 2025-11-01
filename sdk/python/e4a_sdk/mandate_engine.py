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
from datetime import datetime
from jsonschema import validate, ValidationError

SPEC = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'specs', 'mandate_v1.json')

with open(SPEC, 'r') as _f:
    MANDATE_SCHEMA = json.load(_f)


class MandateEngineError(Exception):
    pass


class MandateEngine:
    def __init__(self, scribe=None):
        # in-memory store for Phase 1 (replace with persistence later)
        self.mandates = {}
        self.scribe = scribe

    def validate_mandate(self, mandate):
        try:
            validate(instance=mandate, schema=MANDATE_SCHEMA)
        except ValidationError as e:
            raise MandateEngineError(f"Mandate validation error: {e.message}")

    def create_mandate(self, mandate):
        mandate = dict(mandate)
        if not mandate.get('mandate_id'):
            mandate['mandate_id'] = str(uuid.uuid4())
        mandate.setdefault('created_at', datetime.utcnow().isoformat() + 'Z')

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

        # Phase 1: mock execution — record action and compute fees
        result = {
            'status': 'executed',
            'executor': executor_id,
            'executed_at': datetime.utcnow().isoformat() + 'Z',
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
    from core.scribe_agent import ScribeAgent
    scribe = ScribeAgent()
    engine = MandateEngine(scribe=scribe)

    sample = {
        'issuer': 'did:example:alice',
        'beneficiary': 'did:example:bob',
        'amount': 100.0,
        'currency': 'USD',
        'fee_distribution': {'protocol': 0.01, 'validator': 0.01, 'issuer': 0.01}
    }

    m = engine.create_mandate(sample)
    print('Created mandate:', m['mandate_id'])
    print('Execute result:', engine.execute_mandate(m['mandate_id']))
