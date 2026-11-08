"""
Persistence for the E4A 1.0 reference implementation (spec section 12,
decision D3).

The lifecycle logic depends only on the small store interface below.
Two backends ship:

- ``InMemoryStore`` — process-local, for tests and demos (the prototype's
  behavior, now behind the interface).
- ``SQLiteStore`` — embedded file database for the reference deployment.
  Mandates, gates, states, submissions, and audit records survive restarts.

Persisted data carries the protocol version. Opening a store written by an
unsupported newer major version fails loudly with ``E4A_STORE_VERSION``.
"""

import json
import sqlite3
import threading

from . import errors

SUPPORTED_STORE_MAJOR = 1


def _check_version(found):
    try:
        major = int(str(found).split(".")[0])
    except (TypeError, ValueError):
        major = -1
    if major != SUPPORTED_STORE_MAJOR:
        raise errors.E4AError(
            f"Persisted data protocol version {found!r} is not supported by this "
            f"implementation (major {SUPPORTED_STORE_MAJOR} required)",
            code=errors.STORE_VERSION,
        )


class InMemoryStore:
    """Process-local store. Nothing survives a restart."""

    def __init__(self):
        self._mandates = {}  # mandate_id -> record dict (mandate + state + submission)
        self._gates = {}  # gate_id -> gate dict
        self._audit = {}  # mandate_id -> [audit record]

    # -- mandates ---------------------------------------------------------
    def put_mandate(self, record):
        self._mandates[record["mandate"]["mandate_id"]] = record

    def get_mandate(self, mandate_id):
        return self._mandates.get(mandate_id)

    def find_by_nonce(self, issuer, replay_nonce):
        for record in self._mandates.values():
            m = record["mandate"]
            if m.get("issuer") == issuer and m.get("replay_nonce") == replay_nonce:
                return record
        return None

    def all_mandates(self):
        return list(self._mandates.values())

    # -- gates ------------------------------------------------------------
    def put_gate(self, gate):
        self._gates[gate["gate_id"]] = gate

    def get_gate(self, gate_id):
        return self._gates.get(gate_id)

    def get_gate_by_mandate(self, mandate_id):
        for gate in self._gates.values():
            if gate["mandate_id"] == mandate_id:
                return gate
        return None

    def all_gates(self):
        return list(self._gates.values())

    # -- audit ------------------------------------------------------------
    def append_audit(self, mandate_id, record):
        self._audit.setdefault(mandate_id, []).append(record)

    def get_audit(self, mandate_id):
        return list(self._audit.get(mandate_id, []))


class SQLiteStore:
    """SQLite-backed store for the reference deployment."""

    def __init__(self, path):
        self.path = str(path)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        with self._conn:
            self._conn.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)")
            self._conn.execute("CREATE TABLE IF NOT EXISTS mandates (mandate_id TEXT PRIMARY KEY, record TEXT)")
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS gates (gate_id TEXT PRIMARY KEY, mandate_id TEXT, gate TEXT)"
            )
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS audit (id INTEGER PRIMARY KEY AUTOINCREMENT, mandate_id TEXT, record TEXT)"
            )
            row = self._conn.execute("SELECT value FROM meta WHERE key='protocol_version'").fetchone()
            if row is None:
                self._conn.execute("INSERT INTO meta (key, value) VALUES ('protocol_version', '1.0')")
            else:
                _check_version(row[0])

    def close(self):
        self._conn.close()

    # -- mandates ---------------------------------------------------------
    def put_mandate(self, record):
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT OR REPLACE INTO mandates (mandate_id, record) VALUES (?, ?)",
                (record["mandate"]["mandate_id"], json.dumps(record)),
            )

    def get_mandate(self, mandate_id):
        row = self._conn.execute("SELECT record FROM mandates WHERE mandate_id = ?", (mandate_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def find_by_nonce(self, issuer, replay_nonce):
        for record in self.all_mandates():
            m = record["mandate"]
            if m.get("issuer") == issuer and m.get("replay_nonce") == replay_nonce:
                return record
        return None

    def all_mandates(self):
        rows = self._conn.execute("SELECT record FROM mandates").fetchall()
        return [json.loads(r[0]) for r in rows]

    # -- gates ------------------------------------------------------------
    def put_gate(self, gate):
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT OR REPLACE INTO gates (gate_id, mandate_id, gate) VALUES (?, ?, ?)",
                (gate["gate_id"], gate["mandate_id"], json.dumps(gate)),
            )

    def get_gate(self, gate_id):
        row = self._conn.execute("SELECT gate FROM gates WHERE gate_id = ?", (gate_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def get_gate_by_mandate(self, mandate_id):
        row = self._conn.execute("SELECT gate FROM gates WHERE mandate_id = ?", (mandate_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def all_gates(self):
        rows = self._conn.execute("SELECT gate FROM gates").fetchall()
        return [json.loads(r[0]) for r in rows]

    # -- audit ------------------------------------------------------------
    def append_audit(self, mandate_id, record):
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT INTO audit (mandate_id, record) VALUES (?, ?)",
                (mandate_id, json.dumps(record)),
            )

    def get_audit(self, mandate_id):
        rows = self._conn.execute("SELECT record FROM audit WHERE mandate_id = ? ORDER BY id", (mandate_id,)).fetchall()
        return [json.loads(r[0]) for r in rows]
