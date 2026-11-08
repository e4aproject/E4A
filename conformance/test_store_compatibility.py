"""Spec section 12 conformance: persistence and store compatibility.

- Records persist across implementation instances over the same store.
- A store written by a newer major protocol version MUST fail loudly with
  E4A_STORE_VERSION rather than being silently mis-read. The newer-version
  store is produced by writing the store's own version marker at the file
  level (the SQLite backend is the documented reference store).
"""

import sqlite3

import pytest

from conftest import error_code, state_of, vector_mandate


def test_sqlite_store_persists_across_instances(tmp_path):
    from e4a_sdk import MandateEngine, SQLiteStore

    db = str(tmp_path / "tck-store.db")
    mandate = vector_mandate("valid-minimal.json")
    mandate["replay_nonce"] = "tck-store-1"
    first = MandateEngine(store=SQLiteStore(db))
    created = first.create_mandate(mandate)

    second = MandateEngine(store=SQLiteStore(db))
    fetched = second.get_mandate(created["mandate_id"])
    assert fetched["mandate_id"] == created["mandate_id"]
    assert state_of(fetched) == "created"
    assert second.get_audit(created["mandate_id"]), "audit records persist with the mandate"


def test_newer_store_version_fails_loudly(tmp_path):
    from e4a_sdk import MandateEngine, SQLiteStore

    db = str(tmp_path / "tck-store-version.db")
    engine = MandateEngine(store=SQLiteStore(db))
    engine.create_mandate(vector_mandate("valid-minimal.json"))

    conn = sqlite3.connect(db)
    conn.execute("UPDATE meta SET value='99.0' WHERE key='protocol_version'")
    conn.commit()
    conn.close()

    with pytest.raises(Exception) as excinfo:
        SQLiteStore(db)
    assert error_code(excinfo.value) == "E4A_STORE_VERSION"
