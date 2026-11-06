# Quickstart: The E4A Developer Flow (verified path)

This quickstart documents the flow that **actually works today**, verified
against the current code (see [project-status.md](project-status.md) for the
verification record). E4A is a pre-release prototype: the packaged install is
broken, so this path runs from a **source checkout**. Steps that existed in
earlier versions of this document but do not work are listed under
"Not working yet" at the end — they are not presented as working steps.

## 1. Set up

```bash
git clone https://github.com/e4aproject/E4A.git
cd E4A
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Run the test suite

The SDK package lives under `sdk/python`, so supply its path explicitly:

```bash
PYTHONPATH=sdk/python python -m pytest tests/ -q
```

Expected: **13 passed**.

## 3. Create, execute, and audit a mandate (SDK, in-memory)

Save as `quickstart_demo.py` in the repository root and run it with
`PYTHONPATH=sdk/python python quickstart_demo.py`:

```python
from e4a_sdk.mandate_engine import MandateEngine
from e4a_sdk.scribe_agent import ScribeAgent

scribe = ScribeAgent(log_path="mission_log.jsonl")
engine = MandateEngine(scribe=scribe)

mandate = {
    "issuer": "did:ex:alice",
    "beneficiary": "did:ex:bob",
    "amount": 1,
    "currency": "USD",
    "replay_nonce": "demo-nonce-1",
    "intent": {
        "goal": "demonstrate the mandate lifecycle",
        "expected_outcome": "mandate executed and logged",
        "contextual_tone": "neutral",
        "statistical_purpose": "quickstart verification",
    },
}

created = engine.create_mandate(mandate)
print("created:", created["mandate_id"])

# Re-submitting with the same replay_nonce returns the existing mandate
# (Phase 1 idempotency behavior).
again = engine.create_mandate(mandate)
assert again["mandate_id"] == created["mandate_id"]

result = engine.execute_mandate(created["mandate_id"])
print("execute:", result["status"])  # mock execution — no external effect
```

Then inspect the audit trail: `mission_log.jsonl` contains one JSON record
per event, including `mandate_created` and `mandate_executed`.

**Read the fine print before relying on any of this:**

- This flow validates against `specs/mandate_v2.json`. The `intent` object
  (with `goal`, `expected_outcome`, `contextual_tone`, and
  `statistical_purpose`) is **required** by that schema.
- Execution is a **mock**: no payment, anchoring, or external side effect
  occurs. Storage is **in-memory**; records do not survive a restart.
- Approval gates exist in the SDK (`gate_engine`) but are not wired into this
  minimal flow; enforcement rules are part of the v1 scope lock.

## Not working yet (verified — do not use)

- **Packaged install:** the built wheel cannot be imported in a clean
  environment, and the `e4a` CLI entry point is missing from the
  distribution. (Status doc, findings B5–B7.)
- **A2A adapter mandate creation:** the adapter validates against
  `specs/mandate_v1.json` while the engine requires v2, so the adapter flow
  fails end to end. Which schema is canonical is maintainer decision D1.
- **Anchoring via the Universal Rail Adapter mock server:**
  `adapters/universal_rail_adapter/mock_server.py` does not compile
  (`IndentationError`). Anchoring is deferred from the v1 critical path.
- **`examples/demo_full_run.py`:** imports a `core` package that no longer
  exists and does not run.
- **Schema validation CLI examples** referencing `examples/sample_mandate.json`:
  that file does not exist in the repository.

This document will be replaced by the v1 quickstart — install the built
artifact, run the documented lifecycle — when the packaging and scope-lock
phases land. Until then, if a step here fails, the project status document is
the record of known failures; please open an issue with your environment and
the failing step.
