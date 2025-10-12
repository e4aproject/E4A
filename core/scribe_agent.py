# core/scribe_agent.py
from datetime import datetime, timezone
import json
import uuid
from pathlib import Path


class ScribeAgent:
    """
    The ScribeAgent records events, mandates, and audits to a persistent or in-memory mission log.
    Backward compatible with legacy tests that used 'log_path' and both styles of append_entry().
    """

    def __init__(self, node_id: str = None, log_path: str = None):
        self.node_id = node_id or f"scribe-{uuid.uuid4().hex[:8]}"
        self.ledger = []
        self.log_path = Path(log_path) if log_path else None

        # Prepare log file if needed
        if self.log_path:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            self.log_path.touch(exist_ok=True)

    def record(self, entry_type: str, payload: dict, summary: str):
        """Primary method for writing an entry."""
        entry = {
            "entry_type": entry_type,
            "entry_id": f"entry-{int(datetime.now(timezone.utc).timestamp())}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "node_id": self.node_id,
            "payload": payload,
            "narrative_summary": summary,
        }

        self.ledger.append(entry)
        if self.log_path:
            with open(self.log_path, "a") as f:
                f.write(json.dumps(entry) + "\n")

        return entry

    # ✅ Fully backward-compatible append_entry()
    def append_entry(self, *args, **kwargs):
        """
        Legacy alias for record(). Supports both:
          append_entry(entry_type, payload, summary)
        and
          append_entry(entry_dict)
        """
        # Case 1: single dict-style call
        if len(args) == 1 and isinstance(args[0], dict):
            entry = args[0]
            # Ensure required keys
            entry.setdefault("entry_id", f"entry-{int(datetime.now(timezone.utc).timestamp())}")
            entry.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
            entry.setdefault("node_id", self.node_id)
            self.ledger.append(entry)
            if self.log_path:
                with open(self.log_path, "a") as f:
                    f.write(json.dumps(entry) + "\n")
            return entry

        # Case 2: modern call pattern
        elif len(args) == 3:
            return self.record(*args)

        # Case 3: explicit keyword args
        elif "entry_type" in kwargs and "payload" in kwargs and "summary" in kwargs:
            return self.record(kwargs["entry_type"], kwargs["payload"], kwargs["summary"])

        else:
            raise TypeError("append_entry() must be called with either (dict) or (entry_type, payload, summary)")

    def get_entries(self, entry_type: str = None):
        if entry_type:
            return [e for e in self.ledger if e["entry_type"] == entry_type]
        return self.ledger

    def dump_json(self, path=None):
        path = Path(path or self.log_path or "scribe_ledger.json")
        with open(path, "w") as f:
            json.dump(self.ledger, f, indent=2)
        return str(path)
