"""
Midnight Adapter (simulated)

- create_confidential_contract(payload): simulate creating a private contract, produce anchor_ref (uuid)
- verify_zkproof(proof_ref): check existence in simple store
- publish_anchor(anchor_hash, settlement_hint=None): record proof anchor and optional settlement refs
"""

import json
import os
import uuid
from datetime import datetime, UTC

STORE = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'midnight_store.json')


def _ensure():
    os.makedirs(os.path.dirname(STORE), exist_ok=True)
    if not os.path.exists(STORE):
        with open(STORE, 'w') as fh:
            json.dump({"proofs": {}}, fh)


def _load():
    _ensure()
    with open(STORE, 'r') as fh:
        return json.load(fh)


def _save(state):
    with open(STORE, 'w') as fh:
        json.dump(state, fh, indent=2, default=str)


class MidnightAdapter:
    def __init__(self):
        _ensure()

    def create_confidential_contract(self, payload):
        """
        Simulate creation of a confidential contract and return an anchor_ref.
        """
        state = _load()
        anchor_ref = str(uuid.uuid4())
        state['proofs'][anchor_ref] = {
            "anchor_ref": anchor_ref,
            "payload_summary": {"issuer": payload.get('issuer'), "beneficiary": payload.get('beneficiary')},
            "created_at": datetime.now(UTC).isoformat().replace('+00:00', 'Z')
        }
        _save(state)
        return {"anchor_ref": anchor_ref, "status": "created"}

    def verify_zkproof(self, anchor_ref):
        state = _load()
        ok = anchor_ref in state.get('proofs', {})
        return {"anchor_ref": anchor_ref, "valid": ok}

    def publish_anchor(self, anchor_ref, settlement_ref=None):
        state = _load()
        if anchor_ref not in state.get('proofs', {}):
            return {"status": "error", "reason": "proof_not_found"}
        state['proofs'][anchor_ref]['settlement_ref'] = settlement_ref
        state['proofs'][anchor_ref]['published_at'] = datetime.now(UTC).isoformat().replace('+00:00', 'Z')
        _save(state)
        return {"status": "published", "anchor_ref": anchor_ref, "settlement_ref": settlement_ref}
