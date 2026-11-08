# Quickstart: The E4A Developer Flow (verified path)

This quickstart documents the flow that **actually works today**, verified
against the built distribution artifact (see
[project-status.md](project-status.md) for the verification record). E4A
1.0 is a pre-release governance protocol: identities are *asserted* (no
cryptographic identity in 1.0) and execution is a clearly labelled
**mock** — no real funds or external effects. Read the spec's Purpose and
non-purpose (spec section 1) before building on it.

## 1. Build and install the artifact

From a source checkout (the package is not yet published to PyPI):

```bash
git clone https://github.com/e4aproject/E4A.git
cd E4A
python3 -m venv .venv
source .venv/bin/activate
pip install build
python -m build
pip install dist/*.whl
```

Verify the install — run from any directory *other* than the checkout,
so imports resolve to the installed package:

```bash
e4a version
# e4a-sdk 1.0.1 (protocol 1.0)
python scripts/verify_installed_artifact.py   # from the checkout, using the venv python
```

The verification script imports the installed package, loads the bundled
canonical schemas, and runs a gated mandate lifecycle against a temporary
SQLite store. It must print its `OK` lines.

## 2. Run the mandate lifecycle from the CLI

The CLI drives the SDK in-process and persists to a local SQLite store
(`$E4A_DB_PATH`, default `~/.e4a/e4a.db`), so separate invocations see
the same mandates:

```bash
export E4A_DB_PATH=/tmp/e4a-demo.db

# create a mandate that requires one approval
e4a mandate create --issuer did:ex:alice --beneficiary did:ex:bob \
  --goal "demonstrate the mandate lifecycle" \
  --requires-approval did:ex:carol --nonce demo-1

# approve it, execute it (mock), and read the audit trail
e4a mandate decide <mandate_id> --actor did:ex:carol --decision approve
e4a mandate execute <mandate_id>
e4a mandate audit <mandate_id>
```

Re-running the same `create` with the same `--nonce` (per issuer) returns
the existing mandate instead of creating a duplicate (spec section 6).
Errors are printed as JSON with a stable `E4A_*` code and exit status 1.

## 3. Or run the lifecycle in Python

```python
from e4a_sdk.mandate_engine import MandateEngine
from e4a_sdk.scribe_agent import ScribeAgent

engine = MandateEngine(scribe=ScribeAgent(log_path="mission_log.jsonl"))

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
print("created:", created["mandate_id"], created["status"])
result = engine.execute_mandate(created["mandate_id"])
print("execute:", result["status"])  # mock execution — no external effect
print("audit events:", [e["entry_type"] for e in engine.get_audit(created["mandate_id"])])
```

## 4. Run the reference service

From the installed package:

```bash
e4a serve --port 8000
curl localhost:8000/health
```

or from Docker: see [deployment.md](deployment.md). The `/v1` API is
specified in spec section 11.

## 5. Run the test suite (source checkout)

```bash
pip install -r requirements.txt
python -m pytest tests/ -q
```

## Not in v1 scope (do not rely on)

- **Adapters and anchoring** (`adapters/`, including the Universal Rail
  mock server): prototype code outside the v1 release surface; the mock
  server does not compile and anchoring is deferred.
- **`examples/demo_full_run.py`:** imports a `core` package that no
  longer exists and does not run.
- **Charters, governance, reputation:** present as prototype modules in
  the SDK; the normative 1.0 surface is the mandate lifecycle only (see
  the spec's Purpose and non-purpose).
- **Cryptographic identity and signatures:** not in 1.0 (spec section 9).

If a step here fails, the project status document is the record of known
failures; please open an issue with your environment and the failing step.
