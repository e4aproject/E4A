# E4A 1.0 Conformance Suite (TCK)

This suite checks an implementation of E4A protocol 1.0 against the
**specification**, not against the reference implementation's internals.

## Independence rules

- Every expectation in this suite is derived from
  `docs/protocol/spec.md`, `docs/protocol/mandate.schema.json`, and the
  machine-readable vectors in `docs/protocol/test-vectors/`, which are
  read as data at run time.
- Error codes asserted here are string literals copied from spec
  section 14. This suite never imports `e4a_sdk.errors` or any other
  implementation-internal module.
- Implementations are driven only through public interfaces:
  - the public Python API (top-level `e4a_sdk` exports), and
  - the HTTP API profile (spec section 11), exercised black-box against
    a separately launched service process.

A failure therefore means one of two things, both worth knowing: the
implementation diverges from the spec, or the spec is ambiguous. Either
way, record the outcome in `docs/project-status.md` rather than quietly
editing this suite to match the implementation.

## Running

Preferred — against the **installed artifact** (what Phase 6 verifies):

```bash
python -m build
python -m venv /tmp/tck && /tmp/tck/bin/pip install dist/*.whl pytest httpx jsonschema
cd /tmp && /tmp/tck/bin/python -m pytest /path/to/repo/conformance -q
```

Also supported — from a source checkout (imports resolve to the source
tree via the repo's root `conftest.py`):

```bash
pip install -r requirements.txt pytest httpx jsonschema
python -m pytest conformance/ -q
```

The API-profile tests launch the reference service as a subprocess
(`uvicorn api.server:create_app --factory`) on an ephemeral port with a
temporary database; they need `uvicorn` available in the environment
(it is a declared dependency of the package).

## Coverage map

| Spec section | Suite file |
|---|---|
| Section 3 + schema vectors | `test_schema_vectors.py` |
| Sections 4–8 + lifecycle vectors L1–L8 | `test_lifecycle_vectors.py` |
| Section 10 audit records | `test_audit_requirements.py` |
| Section 11 API profile | `test_api_profile.py` |
| Section 12 persistence & store version | `test_store_compatibility.py` |
