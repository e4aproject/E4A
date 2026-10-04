import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


class ScribeAgent:
    """Record tamper-evident ledger entries for mandates, governance, and agent events."""

    def __init__(self, node_id: str = None, log_path: str = None):
        self.node_id = node_id or f"scribe-{uuid.uuid4().hex[:8]}"
        self.ledger = []
        self.log_path = Path(log_path) if log_path else None
        self.last_hash = None

        if self.log_path:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            self.log_path.touch(exist_ok=True)

    @staticmethod
    def _canonical_json(obj):
        return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)

    def _compute_hash(self, entry: dict) -> str:
        entry_copy = dict(entry)
        entry_copy.pop("hash", None)
        entry_copy.pop("previous_hash", None)
        return hashlib.sha256(self._canonical_json(entry_copy).encode("utf-8")).hexdigest()

    def record(self, entry_type: str, payload: dict, summary: str):
        entry = {
            "entry_type": entry_type,
            "entry_id": f"entry-{int(datetime.now(timezone.utc).timestamp() * 1000)}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "node_id": self.node_id,
            "payload": payload,
            "narrative_summary": summary,
            "previous_hash": self.last_hash,
        }
        entry["hash"] = self._compute_hash(entry)
        self.ledger.append(entry)
        self.last_hash = entry["hash"]
        if self.log_path:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, default=str) + "\n")
        return entry

    def append_entry(self, *args, **kwargs):
        if len(args) == 1 and isinstance(args[0], dict):
            entry = dict(args[0])
            entry.setdefault("entry_id", f"entry-{int(datetime.now(timezone.utc).timestamp() * 1000)}")
            entry.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
            entry.setdefault("node_id", self.node_id)
            entry.setdefault("previous_hash", self.last_hash)
            entry["hash"] = self._compute_hash(entry)
            self.ledger.append(entry)
            self.last_hash = entry["hash"]
            if self.log_path:
                with open(self.log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry, default=str) + "\n")
            return entry

        if len(args) == 3:
            return self.record(*args)

        if "entry_type" in kwargs and "payload" in kwargs and "summary" in kwargs:
            return self.record(kwargs["entry_type"], kwargs["payload"], kwargs["summary"])

        raise TypeError("append_entry() must be called with either (dict) or (entry_type, payload, summary)")

    def get_entries(self, entry_type: str = None):
        if entry_type:
            return [entry for entry in self.ledger if entry["entry_type"] == entry_type]
        return self.ledger

    def verify_chain(self):
        previous_hash = None
        for entry in self.ledger:
            if entry.get("previous_hash") is not None and entry.get("previous_hash") != previous_hash:
                return False
            expected_hash = self._compute_hash(entry)
            if entry.get("hash") != expected_hash:
                return False
            previous_hash = entry.get("hash")
        return True

    def dump_json(self, path=None):
        path = Path(path or self.log_path or "scribe_ledger.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.ledger, f, indent=2, default=str)
        return str(path)


__all__ = ["ScribeAgent"]
