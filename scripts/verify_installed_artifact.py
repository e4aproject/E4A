#!/usr/bin/env python3
"""Verify an *installed* e4a-sdk artifact (wheel or sdist install).

Run this from a clean virtual environment with the built distribution
installed, from a working directory that is NOT the repository checkout,
so imports resolve to site-packages:

    python -m build
    python -m venv /tmp/e4a-clean && /tmp/e4a-clean/bin/pip install dist/*.whl
    cd /tmp && /tmp/e4a-clean/bin/python /path/to/scripts/verify_installed_artifact.py

Checks: package import and version, bundled canonical schema loads,
a full mandate lifecycle against a temporary SQLite store (create with
an approval gate, decide, execute, audit), and idempotent re-submission.
Prints OK lines and exits non-zero on the first failure.
"""

import sys
import tempfile
from pathlib import Path

import e4a_sdk
from e4a_sdk import PROTOCOL_VERSION, __version__
from e4a_sdk.mandate_engine import MandateEngine
from e4a_sdk.schema import GATE_SCHEMA, MANDATE_SCHEMA
from e4a_sdk.scribe_agent import ScribeAgent
from e4a_sdk.store import SQLiteStore


def main() -> int:
    print(f"e4a_sdk {__version__} (protocol {PROTOCOL_VERSION}) imported from {Path(e4a_sdk.__file__).parent}")
    if "site-packages" not in str(Path(e4a_sdk.__file__)) and "dist-packages" not in str(Path(e4a_sdk.__file__)):
        print("FAIL: e4a_sdk did not import from an installed location", file=sys.stderr)
        return 1
    assert MANDATE_SCHEMA and GATE_SCHEMA, "bundled schemas failed to load"
    print("bundled canonical schemas: OK")

    with tempfile.TemporaryDirectory() as tmp:
        db = str(Path(tmp) / "verify.db")
        scribe = ScribeAgent(node_id="verify", log_path=str(Path(tmp) / "log.jsonl"))
        engine = MandateEngine(store=SQLiteStore(db), scribe=scribe)
        mandate = {
            "issuer": "did:ex:alice",
            "beneficiary": "did:ex:bob",
            "amount": 5,
            "currency": "USD",
            "replay_nonce": "verify-nonce-1",
            "intent": {
                "goal": "verify the installed artifact end to end",
                "expected_outcome": "mandate executed with a complete audit trail",
                "contextual_tone": "neutral",
                "statistical_purpose": "release verification",
                "requires_approval": ["did:ex:carol"],
            },
        }
        created = engine.create_mandate(mandate)
        assert created["status"] == "pending_approval", created
        again = engine.create_mandate(mandate)
        assert again["mandate_id"] == created["mandate_id"], "idempotent re-submission failed"
        decided = engine.record_decision(created["mandate_id"], "did:ex:carol", "approve")
        assert decided["status"] == "approved", decided
        executed = engine.execute_mandate(created["mandate_id"])
        assert executed["status"] == "executed", executed
        event_types = [e["entry_type"] for e in engine.get_audit(created["mandate_id"])]
        for expected in ("mandate_created", "gate_created", "gate_approved", "mandate_executed"):
            assert expected in event_types, f"missing audit event {expected}: {event_types}"
    print("installed-artifact lifecycle (create -> approve -> execute -> audit): OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
