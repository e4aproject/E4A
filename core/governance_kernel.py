"""
Governance Kernel - minimal skeleton for Phase 2.
Responsibilities:
- register charters
- submit proposals
- simulate votes and enact proposals (mocked voting)
- simple persistence in data/governance_state.json
"""
import os
import json
from datetime import datetime, timezone
from typing import Dict, Any

STATE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'governance_state.json')

def _ensure():
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    if not os.path.exists(STATE_PATH):
        with open(STATE_PATH, 'w') as fh:
            json.dump({'charters': {}, 'proposals': {}}, fh)

def _load():
    _ensure()
    with open(STATE_PATH, 'r') as fh:
        return json.load(fh)

def _save(state):
    with open(STATE_PATH, 'w') as fh:
        json.dump(state, fh, indent=2, default=str)

class GovernanceKernel:
    def __init__(self):
        _ensure()
        self.state = _load()

    def register_charter(self, charter_id: str, charter_doc: Dict[str, Any]):
        self.state = _load()
        self.state['charters'][charter_id] = {
            'charter_id': charter_id,
            'doc': charter_doc,
            'registered_at': datetime.now(timezone.utc).isoformat()
        }
        _save(self.state)
        return self.state['charters'][charter_id]

    def submit_proposal(self, charter_id: str, proposal_id: str, proposal: Dict[str, Any]):
        self.state = _load()
        if charter_id not in self.state['charters']:
            raise ValueError('charter not registered')
        self.state['proposals'][proposal_id] = {
            'proposal_id': proposal_id,
            'charter_id': charter_id,
            'proposal': proposal,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'votes': {}
        }
        _save(self.state)
        return self.state['proposals'][proposal_id]

    def vote(self, proposal_id: str, voter_id: str, vote: str):
        self.state = _load()
        if proposal_id not in self.state['proposals']:
            raise ValueError('proposal not found')
        self.state['proposals'][proposal_id]['votes'][voter_id] = vote
        _save(self.state)
        return self.state['proposals'][proposal_id]

    def simulate_and_enact(self, proposal_id: str, quorum: int = 1):
        """Simple simulation: enact if number of votes >= quorum and majority 'yes'."""
        self.state = _load()
        prop = self.state['proposals'].get(proposal_id)
        if not prop:
            raise ValueError('proposal not found')
        votes = prop.get('votes', {})
        if len(votes) < quorum:
            return {'status': 'rejected', 'reason': 'quorum_not_met', 'votes': votes}
        yes = sum(1 for v in votes.values() if v.lower() in ('yes', 'y', 'approve'))
        no = sum(1 for v in votes.values() if v.lower() in ('no', 'n', 'reject'))
        if yes > no:
            prop['enacted_at'] = datetime.now(timezone.utc).isoformat()
            prop['status'] = 'enacted'
            _save(self.state)
            return {'status': 'enacted', 'proposal': prop}
        else:
            prop['status'] = 'rejected'
            _save(self.state)
            return {'status': 'rejected', 'proposal': prop}
