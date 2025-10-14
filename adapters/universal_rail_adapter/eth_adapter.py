"""
Ethereum Adapter (simulated)

- submit_anchor(proof_hash) -> returns a fake tx_hash
- query_anchor(tx_hash) -> returns stored mapping
"""

import json
import os
import uuid
from datetime import datetime

STORE = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'chain_anchors.json')


def _ensure():
    os.makedirs(os.path.dirname(STORE), exist_ok=True)
    if not os.path.exists(STORE):
        with open(STORE, 'w') as fh:
            json.dump({"anchors": {}}, fh)


def _load():
    _ensure()
    with open(STORE, 'r') as fh:
        return json.load(fh)


def _save(state):
    with open(STORE, 'w') as fh:
        json.dump(state, fh, indent=2, default=str)


class EthAdapter:
    def __init__(self, chain_name='ethereum'):
        self.chain = chain_name
        _ensure()

    def submit_anchor(self, proof_hash):
        state = _load()
        tx_hash = f"0x{uuid.uuid4().hex[:32]}"
        state['anchors'][tx_hash] = {
            "proof_hash": proof_hash,
            "chain": self.chain,
            "tx_hash": tx_hash,
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }
        _save(state)
        return {"status": "submitted", "tx_hash": tx_hash}

    def query_anchor(self, tx_hash):
        state = _load()
        return state['anchors'].get(tx_hash)
