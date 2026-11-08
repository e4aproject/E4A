# E4A 1.0 Security & Operational Review (Phase 8)

**Date:** 2026-11-07. **Scope:** the v1 normative surface — the reference
SDK lifecycle, the `/v1` HTTP service, its legacy compatibility routes,
the SQLite/in-memory stores, and the documented deployment. Legacy
prototype components (adapters, governance simulations, validator
runtime) are outside the v1 surface and are classified, not audited.
**Method:** code inspection of the shipped surface, the Phase 6 quality
gates (bandit), `pip-audit` over the dependency set, targeted behavior
tests (this phase's `tests/test_security_review.py`), and the Phase 7
conformance suite as protocol-level evidence. This is an engineering
review, not an independent audit; the spec's own limit stands — **1.0
provides no cryptographic authenticity and must not govern real funds
or high-impact actions** (spec section 9).

## Findings

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| F1 | **High** (for token-configured deployments) | The API token gated only `/v1`. The legacy routes (`/mandates/create`, `/mandates/execute/{id}`, `/gates/*`, `/governance/*`, `/reputation`) operated on the same store with **no authentication**: with a token set, an unauthenticated caller could still create and execute mandates (verified: `/v1` create → 401, legacy create → 200, legacy execute → 200). | **Fixed.** The same token dependency now guards every route except `/health` and `/ready`. Regression tests: `tests/test_security_review.py`. |
| F2 | Low | Token comparison used plain string inequality (timing side channel, minor for a shared-secret gate). | **Fixed** in the same change: `hmac.compare_digest`. |
| F3 | Low | No request-body size limit or rate limiting in the reference service. | **Accepted for v1 scope** (trusted-network/local reference deployment); mitigate at the reverse proxy. Documented here and in `docs/deployment.md`. |
| F4 | Info | Malformed-JSON requests receive FastAPI's framework 422 shape, not the spec section 11 error envelope (the envelope covers protocol errors). | Documented; no change. Clients must handle both. |
| F5 | Info | Dockerfile / docker-compose still not build-verified: the review environment has no container runtime. The image runs the same uvicorn command verified in every other environment. | Carried to Phase 9 with the exact commands (`docker compose up --build`, then the quickstart against `localhost:8000`). |
| F6 | Info | The prototype `E4AClient` speaks only the legacy API and has no token support; with a token configured it can read nothing and write nothing. | Documented limitation. `/v1` is the normative client surface; the CLI (Phase 6) works in-process and is unaffected. |

No critical or high findings remain open for the v1 scope after the F1
fix.

## Documented-control classification (re-verified 2026-11-07)

Updates the Phase 1 baseline table in `docs/security.md`.

| ID | Mitigation | Classification | Evidence |
|---|---|---|---|
| T1 | `replay_nonce` replay protection | **Implemented and tested** (mandate submissions — the v1 normative surface) | Per-(issuer, nonce) uniqueness with idempotent replay and `E4A_NONCE_CONFLICT`, persisted in the store. Unit tests (`tests/test_protocol_vectors.py`, L6) and TCK lifecycle vectors. The original wording "on all verifiable artifacts" remains broader than 1.0: gates do not carry independent nonces. |
| T2 | Validator quorum / staking / attestations | **Not supported** | Simulation only in the governance prototype; outside the v1 surface. Unchanged from baseline. |
| T3 | KMS / key management / rotation | **Not supported — by design** | Decision D2: 1.0 has no keys or signatures to manage. |
| T4 | Governance-capture protections (staged upgrades, rollback) | **Deferred** | Governance kernel remains a prototype skeleton; outside the v1 normative surface. |
| T5 | Rail fail-over / reconciliation | **Not supported** | Adapters are outside the v1 surface; the URA mock server still does not compile. Unchanged from baseline. |
| T6 | Audit integrity (`content_hash`, signed/anchored attestations) | **Partially implemented** | Audit records carry the spec section 10 fields and are append-only within the store's interface (no update/delete path) — TCK `test_audit_requirements.py`. The optional hash-chain extension is **not** implemented in the runtime audit path (a standalone canonicalizer tool exists in `tools/`); signatures and anchoring are not implemented (D2). Plain storage provides no tamper evidence — deployments must not claim otherwise. |

## Service-level controls (not in the original T-table)

| Control | Classification | Evidence |
|---|---|---|
| API token gate (when `E4A_API_TOKEN` configured) | **Implemented and tested** | All routes except `/health`/`/ready` require the bearer token (F1 fix); constant-time compare (F2). TCK `test_configured_token_is_enforced`; `tests/test_security_review.py`. When no token is configured the service is open — development mode, called out in `docs/deployment.md`. |
| Approver authorization (spec section 8) | **Implemented and tested** | Only listed approvers may decide; others get `E4A_UNAUTHORIZED_APPROVER` with no state change. TCK L3 + API profile tests. |
| Input validation | **Implemented and tested** | One canonical schema validation path for every submission (engine, API, adapter). Schema vectors via engine + TCK. |
| Error handling | **Implemented and tested** | Spec envelope `{error: {code, message}}`; no stack traces or internal paths in responses (`tests/test_security_review.py`). |
| SQL handling in the SQLite store | **Implemented** (inspection) | All queries parameterized; no string-built SQL in `e4a_sdk/store.py`. |
| Store-version guard | **Implemented and tested** | Newer-major stores fail with `E4A_STORE_VERSION` (TCK `test_store_compatibility.py`). |
| Transport security (TLS) | **Deployment responsibility** | The reference service serves plain HTTP; run behind a TLS-terminating proxy on any untrusted network — the bearer token is sniffable otherwise. Stated in `docs/deployment.md`. |
| Secrets handling | **Implemented** (inspection) | The token comes only from the environment; no credentials are stored in the repository (bandit clean). |

## Operational verification

| Check | Result |
|---|---|
| Test suite | 54 passed (49 + 5 Phase 8 regression tests) |
| Conformance suite | 35 passed in-repo and against the installed wheel (re-run after the F1 fix) |
| bandit (shipped code) | 0 issues |
| pip-audit (requirements set) | No known vulnerabilities (2026-11-07) |
| Backup / restore | File-copy backup of the SQLite database restores mandates and audit records into a fresh service instance — `tests/test_security_review.py::test_backup_restore_by_file_copy` |
| Restart persistence | Covered by TCK API restart test and Phase 5 integration tests |
| Bad database path | Store creates parent directories (`_make_store`); `:memory:` mode logs a non-persistence warning |
| Docker build / compose up | **Not verified** — no container runtime in the review environment (F5, Phase 9) |
