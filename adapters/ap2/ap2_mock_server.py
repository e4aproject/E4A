"""
AP2 Mock Server (local simulator)
Provides a simple in-process simulator for AP2 create/sign/submit flows.
State stored in data/ap2_mock_store.json
"""

import json
import os
import uuid
from datetime import datetime

STORE_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'ap2_mock_store.json')


def _ensure_store():
    d = os.path.dirname(STORE_PATH)
    os.makedirs(d, exist_ok=True)
    if not os.path.exists(STORE_PATH):
        with open(STORE_PATH, 'w') as fh:
            json.dump({"mandates": {}, "submissions": {}}, fh)


def _load():
    _ensure_store()
    with open(STORE_PATH, 'r') as fh:
        return json.load(fh)


def _save(state):
    with open(STORE_PATH, 'w') as fh:
        json.dump(state, fh, indent=2, default=str)


class AP2MockServer:
    def __init__(self):
        _ensure_store()

    def create(self, mandate_payload):
        state = _load()
        mandate_id = mandate_payload.get('mandate_id') or str(uuid.uuid4())
        mandate_payload['mandate_id'] = mandate_id
        mandate_payload['created_at'] = datetime.utcnow().isoformat() + 'Z'
        state['mandates'][mandate_id] = mandate_payload
        _save(state)
        return {"status": "created", "mandate_id": mandate_id}

    def sign(self, mandate_id, signer="mock-signer"):
        state = _load()
        if mandate_id not in state['mandates']:
            return {"status": "error", "reason": "mandate_not_found"}
        sig = f"sig-{signer}-{mandate_id}"
        state['mandates'][mandate_id].setdefault('signatures', []).append(sig)
        _save(state)
        return {"status": "signed", "signature": sig}

    def submit(self, mandate_id):
        state = _load()
        if mandate_id not in state['mandates']:
            return {"status": "error", "reason": "mandate_not_found"}
        submission_id = str(uuid.uuid4())
        state['submissions'][submission_id] = {
            "submission_id": submission_id,
            "mandate_id": mandate_id,
            "submitted_at": datetime.utcnow().isoformat() + 'Z',
            "status": "settled"
        }
        _save(state)
        return {"status": "settled", "submission_id": submission_id}
