"""
ScribeAgent - simple mission log writer for Phase 1

- Appends JSON Lines into data/mission_log.jsonl
- Generates a simple narrative summary for each entry (placeholder)
"""

import json
import os
from datetime import datetime

DEFAULT_LOG = os.path.join(os.path.dirname(__file__), '..', 'data', 'mission_log.jsonl')


class ScribeAgent:
    def __init__(self, log_path=None):
        self.log_path = log_path or DEFAULT_LOG
        # ensure directory exists
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        if not os.path.exists(self.log_path):
            open(self.log_path, 'w').close()

    def append_entry(self, entry):
        entry = dict(entry)
        entry.setdefault('entry_id', f"entry-{int(datetime.utcnow().timestamp())}")
        entry.setdefault('timestamp', datetime.utcnow().isoformat() + 'Z')
        entry.setdefault('narrative_summary', self.generate_narrative_summary(entry))
        with open(self.log_path, 'a') as fh:
            fh.write(json.dumps(entry) + '\n')
        return entry

    def generate_narrative_summary(self, entry):
        et = entry.get('entry_type', 'event')
        if et == 'mandate_created':
            m = entry.get('payload', {})
            return f"Mandate created by {m.get('issuer')} for {m.get('beneficiary')} (id={m.get('mandate_id')})"
        if et == 'mandate_executed':
            return f"Mandate {entry.get('mandate_id')} executed by {entry.get('executor')}"
        return entry.get('narrative_summary', f"{et} recorded")
