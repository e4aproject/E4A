"""
Validator Runtime - Phase 1 reference (lightweight, non-networked)
Provides:
- start_node() bootstrap (no network)
- reflexivity_tick(): analyze recent mission_log entries and emit meta_audit entries
- listen_quarantine_flags(): scan for quarantine flags (placeholder)
"""

import os
import json
from datetime import datetime, timedelta
from jsonschema import validate, ValidationError

LOG_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'mission_log.jsonl')
SPEC = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'specs', 'mandate_v2.json')

with open(SPEC, 'r') as _f:
    MANDATE_SCHEMA = json.load(_f)


class ValidatorRuntime:
    def __init__(self, node_id='validator-1', log_path=None):
        self.node_id = node_id
        self.log_path = log_path or LOG_PATH

    def start_node(self):
        print(f"Starting validator node {self.node_id} (phase 1 reference)")

    def validate_mandate(self, mandate):
        try:
            validate(instance=mandate, schema=MANDATE_SCHEMA)
        except ValidationError as e:
            raise ValueError(f"Mandate validation error: {e.message}")

    def _read_recent_entries(self, window_seconds=3600):
        entries = []
        if not os.path.exists(self.log_path):
            return entries
        cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)
        with open(self.log_path, 'r') as fh:
            for line in fh:
                try:
                    obj = json.loads(line)
                    ts = obj.get('timestamp')
                    if ts:
                        ts_dt = datetime.fromisoformat(ts.replace('Z', ''))
                        if ts_dt >= cutoff:
                            entries.append(obj)
                except Exception:
                    continue
        return entries

    def reflexivity_tick(self, window_seconds=3600):
        entries = self._read_recent_entries(window_seconds=window_seconds)
        counts = {}
        for e in entries:
            et = e.get('entry_type', 'unknown')
            counts[et] = counts.get(et, 0) + 1
        meta = {
            'entry_type': 'meta_audit',
            'node_id': self.node_id,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'summary': {
                'counts': counts,
                'total_recent': len(entries)
            }
        }
        # append to mission_log
        with open(self.log_path, 'a') as fh:
            fh.write(json.dumps(meta) + '\n')
        return meta

    def listen_quarantine_flags(self):
        flags = []
        if not os.path.exists(self.log_path):
            return flags
        with open(self.log_path, 'r') as fh:
            for line in fh:
                try:
                    obj = json.loads(line)
                    if obj.get('entry_type') in ('quarantine', 'quarantine_flag'):
                        flags.append(obj)
                except Exception:
                    continue
        return flags


if __name__ == '__main__':
    vr = ValidatorRuntime()
    vr.start_node()
    print('Running reflexivity tick...')
    print(vr.reflexivity_tick())
