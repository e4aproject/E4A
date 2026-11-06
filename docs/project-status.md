# E4A Project Status

**Purpose:** This document is the durable, evidence-based record of the verified
state of the E4A repository on the road to a v1 release candidate. A task is
"done" only when its acceptance criteria are met and evidence is recorded here.
Completion is never inferred from a roadmap, a plan document, or a commit
message.

**Branch:** `protocol/v1-road-to-release`
**Baseline commit:** `dbd3e1b` ("fix: Configure NPM publishing with OIDC", 2025-11-11)
**Baseline verified:** 2026-11-05 (America/Chicago), local clone, Python 3.12.3
venv (CI is configured for Python 3.11; version-specific results may differ).

---

## 1. Baseline results (actually executed, not inferred)

| # | Check | Command / method | Result |
|---|-------|------------------|--------|
| B1 | Repository state | `git log -1`, GitHub API | Default branch `main` at `dbd3e1b` (2025-11-11). 0 open issues. 5 open PRs, all Dependabot semantic-release (npm tooling) bumps (#12–#16). |
| B2 | Test suite as a new contributor would run it | `pip install -r requirements.txt`, then `pytest tests/` from repo root | **FAIL at collection:** `ModuleNotFoundError: No module named 'e4a_sdk'` (tests/test_cli_sdk.py). The package lives under `sdk/python` and nothing installs it or puts it on `sys.path`. |
| B3 | Test suite with package path supplied manually | `PYTHONPATH=sdk/python pytest tests/ -q` | **13 passed.** The test logic is largely sound; the failure is packaging/path configuration. |
| B4 | CI equivalence | `.github/workflows/ci.yml` inspected; its steps replicated locally | CI installs only `requirements.txt` and runs `coverage run -m pytest` with no `PYTHONPATH` and no package install, so the test job is expected to fail the same way as B2. The quality job runs flake8/black before tests (see B7). Live Actions status on `main` was **not** independently confirmed during baseline. |
| B5 | Package build | `python -m build --wheel` | Wheel builds (`e4a_sdk-1.0.1-py3-none-any.whl`) but contains **only** the `e4a_sdk` package: no `cli` package, no `api`/`adapters`, and **no JSON schemas**. |
| B6 | Clean install of the built wheel | Fresh venv, `pip install <wheel>`, then import and run | **FAIL:** `import e4a_sdk` raises `FileNotFoundError: .../site-packages/e4a_sdk/../../../specs/gate_v1.json`. Engines load schemas at import time via paths relative to the source tree (`specs/*.json` lives outside the package). |
| B7 | Declared CLI entry point | `e4a --help` from the clean install (B6) | **FAIL:** `ModuleNotFoundError: No module named 'cli'`. `pyproject.toml` declares `e4a = "cli.cli_main:cli"`, but `[tool.setuptools.packages.find]` only searches `sdk/python`, so `cli` is not distributed. |
| B8 | Quickstart end-to-end example | `docs/quickstart.md` step 1 mandate passed through the A2A adapter and the mandate engine from a source checkout | **FAIL:** the quickstart's own example mandate is rejected by the mandate engine with `Mandate validation error: 'intent' is a required property`. The adapter validates against `specs/mandate_v1.json`; the engine validates against `specs/mandate_v2.json`. |
| B9 | Quickstart step 4 (mock anchoring server) | `python -m py_compile adapters/universal_rail_adapter/mock_server.py` | **FAIL:** `IndentationError: unexpected indent` (line 5). The file does not compile. |
| B10 | Lint / format state | `flake8 .`, `black --check .` from repo root | flake8 reports ~61 issues. black would reformat 24 files; 1 file fails to reformat (B9). CI's quality job is therefore expected to fail before tests run. |

## 2. Structural findings (verified by inspection)

| # | Finding | Evidence |
|---|---------|----------|
| S1 | **Schema split.** Two mandate schemas exist. `specs/mandate_v2.json` = v1 + one additional required field, `intent`. Engine and validator runtime load v2; the A2A adapter loads v1. There is no declared canonical version. | `specs/mandate_v1.json`, `specs/mandate_v2.json`; `sdk/python/e4a_sdk/mandate_engine.py` (`SPEC = .../specs/mandate_v2.json`); `sdk/python/e4a_sdk/validator_runtime.py`; `adapters/a2a/adapter.py` (`MANDATE_SCHEMA = _load_schema("mandate_v1.json")`) |
| S2 | **Two import conventions coexist.** Package-internal and CLI code use `e4a_sdk.*`; `api/`, `adapters/`, and some tests use `sdk.python.e4a_sdk.*`, which only resolves inside a source checkout with the repo root on `sys.path`. | `api/server.py` lines 3–7; `adapters/a2a/adapter.py` lines 8–10; `tests/test_cardano_midnight_bridge.py` lines 1–4; contrast `cli/cli_main.py` line 9 |
| S3 | **Schemas are loaded from outside the package** at import time via `../../../specs/*.json` relative paths, making the installed artifact unusable (B6) and coupling the SDK to the repo layout. | `sdk/python/e4a_sdk/mandate_engine.py`, `gate_engine.py` (gate_v1.json), `validator_runtime.py` |
| S4 | **Mandate engine is Phase 1 by its own description:** in-memory store, mock execution, fee-split computation; idempotency is a simple `replay_nonce` scan. | `sdk/python/e4a_sdk/mandate_engine.py` module docstring and `create_mandate` |
| S5 | **Governance kernel is a self-described skeleton:** simulated voting, local JSON persistence at `sdk/python/data/governance_state.json`. | `sdk/python/e4a_sdk/governance_kernel.py` module docstring |
| S6 | **Empty (0-byte) modules and artifacts**, including `sdk/python/e4a_sdk/charter_engine.py`, `sdk/python/e4a_sdk/evolution_engine.py`, `adapters/universal_rail_adapter/cardano_adapter.py`, `adapters/universal_rail_adapter/fabric_adapter.py`, `adapters/a2a/aries_adapter.py`, `cultural/audits/cultural_audit.py`, `cultural/charters/charter.yaml`, `governance/voting_rules.yaml`, `governance/pef_spec.md`, `tests/simulation/cultural_drift_sim.py`, and a stray file named `CHANGELOG.md ` (trailing space) alongside the real `CHANGELOG.md` (542 bytes). | `git ls-files` + file sizes at `dbd3e1b` |
| S7 | **Version drift.** Python package declares 1.0.1 (`pyproject.toml`, `sdk/python/e4a_sdk/__version__.py`); npm `package.json` declares 1.0.0. Release automation is npm/semantic-release-centric (see the Dependabot backlog, B1). | `pyproject.toml`, `package.json` |
| S8 | **Documentation/planning sources conflict.** `ROADMAP.md` marks Phase 1.5 "Complete" and the reference implementation "Upcoming"; `plans/E4A_v1.1.yml` lists phase deliverables (including a "mandate_v1_schema_lock") with no completion state; the code already contains a partial implementation. No document currently governs scope/status. | `ROADMAP.md` (updated 2025-11-01), `plans/E4A_v1.1.yml` |
| S9 | **Quickstart documentation is not runnable as written** (B8, B9) and contains literal escaped code fences (`\`\`\`python`), indicating it was not executed after editing. | `docs/quickstart.md` |
| S10 | **`examples/demo_full_run.py` does not run:** it imports `from core.scribe_agent import ScribeAgent` — no `core` package exists in the current layout. Verified by execution (Phase 2). | `examples/demo_full_run.py` line 2 |
| S11 | **Release workflow auto-publishes:** `.github/workflows/release.yml` publishes to PyPI and npm on every push to `main`, gated only by the quality/test jobs (currently expected to fail — see B4/B10). `CONTRIBUTING.md`'s claim is therefore accurate about the workflow but the arrangement is unsafe until release engineering (Phase 6) replaces it with an explicit approval step. | `.github/workflows/release.yml`; `docs/PUBLISHING.md` |
| S12 | **Security mitigations classified** (Phase 2 verification of `docs/security.md` against code): T1 replay nonce — partially implemented (in-memory scan in the mandate engine); T6 — partially implemented (SHA-256 canonicalization tool + local JSONL scribe log; no signatures or anchoring); T2 — not supported (quorum exists only as a parameter of simulated governance voting); T3 — not supported (no key code at all); T4 — deferred (skeleton; PEF spec is an empty file); T5 — not supported (adapters empty/mocks). Full table in `docs/security.md`. | `docs/security.md` implementation-status table |

## 3. Prioritized issue inventory

| Priority | Issue | Source |
|----------|-------|--------|
| P0 | Installed package cannot be imported (schema paths outside package; schemas not distributed) | B6, S3 |
| P0 | Declared CLI entry point is not in the distribution | B7, B5 |
| P0 | No canonical mandate schema version; quickstart flow fails end to end | B8, S1 |
| P0 | Test suite fails as documented / as CI runs it | B2, B4 |
| P1 | Dual import conventions tie code to the source-checkout layout | S2 |
| P1 | Quickstart mock server does not compile | B9 |
| P1 | Lint/format state fails CI quality gates | B10 |
| P1 | Security properties in `docs/security.md` are documented, not demonstrated in code/tests — must be classified (implemented / partial / extension / deferred) before any are claimed | Assessment review; verification is Phase 8 work |
| P2 | Empty modules/artifacts create a false impression of implemented features | S6 |
| P2 | Version drift between Python and npm packages; release process is npm-centric while the reference implementation is Python | S7, B1 |
| P2 | Multiple planning documents with conflicting status; no single source of truth | S8 |

## 4. Phase tracking

| Phase | Status | Evidence | Acceptance criteria | Blockers | Last verified |
|-------|--------|----------|---------------------|----------|---------------|
| 1. Inspect & baseline | Done | This document; baseline table §1; draft PR #17 | Baseline recorded with commands and failures; prioritized issue inventory exists | None | 2026-11-05 |
| 2. Documentation system & governance | Done | README maturity note + doc map; ROADMAP rewritten with exit criteria + history; `docs/protocol/README.md` (marked not-yet-normative); quickstart rewritten to the executed flow (script extracted and run: create → idempotent re-submit → mock execute → `mandate_created`/`mandate_executed` in the JSONL log) with a verified "not working yet" list; `docs/security.md` implementation-status table (S12); CONTRIBUTING corrected to the real branching model + release-automation warning (S11); ONBOARDING reading order; CHANGELOG [Unreleased]; status header on `plans/E4A_v1.1.yml`; status banners on `docs/E4A_Level2.1_Validated.md` and `docs/THREAT_MODEL_V2.md`; MkDocs nav extended | One authoritative doc map; no active doc claims unverified functionality as complete/secure/production-ready | None | 2026-11-05 |
| 3. Lock v1 scope & protocol contract | Not started | — | Canonical schema/version chosen; lifecycle, errors, idempotency, approval, audit, and signature decision specified with test vectors | Maintainer decisions D1–D4 (§5) | — |
| 4. Repair reference SDK | Not started | — | One validation path; lifecycle enforced; tests for valid/invalid, transitions, approval, expiry, duplicates, persistence, audit | Phase 3 gate | — |
| 5. Deployable reference service | Not started | — | Versioned API, health/readiness, persistent storage, container local deployment, restart-persistence verified by integration tests | Phase 4; decision D4 | — |
| 6. Package & release engineering | Not started | — | Clean-env install of the *built artifact* passes import, CLI, and quickstart; CI tests the artifact | Phase 4–5 | — |
| 7. Conformance suite (TCK) | Not started | — | Independent suite validates protocol behavior from schemas/vectors/public interfaces; reference implementation passes | Phase 3, 4 | — |
| 8. Security & operational review | Not started | — | Every documented control classified with test evidence; no unresolved critical issue for v1 scope | Phase 4–5 | — |
| 9. External-user verification & RC | Not started | — | Clean user completes install/deploy/quickstart/TCK from docs alone; RC ready for human approval; nothing published without approval | All prior phases | — |

## 5. Decisions needed from the maintainer

| # | Decision | Why it matters | Recommendation (for maintainer approval) |
|---|----------|----------------|------------------------------------------|
| D1 | Canonical mandate schema: v1 or v2? | Every code path, the spec, and the TCK depend on one answer (S1, B8) | Adopt **v2** as canonical v1-of-record (a mandate without an `intent` is hard to govern) and version the protocol explicitly going forward |
| D2 | Are cryptographic signatures in v1 scope? | Determines the trust model, spec surface, and security claims | If not implemented and tested, state plainly that v1 provides no cryptographic authenticity and defer signing to a later version |
| D3 | Persistence backend for the reference implementation/deployment | Engine is in-memory today (S4); deployment phase needs a defined store | Define a persistence interface in the SDK; ship one documented local backend (e.g., SQLite or JSON-file) for the reference deployment |
| D4 | How much API service is in v1 scope? | `api/server.py` exists but is tied to checkout-only imports (S2) | Include a minimal versioned API over the mandate lifecycle as the interoperability demo; defer validator-network services |

## 6. Guardrails for this work

- All work happens on `protocol/v1-road-to-release` or successor branches; no direct pushes to `main`.
- Nothing is published, released, tagged, or deployed publicly without explicit maintainer approval.
- No feature is described as implemented based on documentation alone; status claims require evidence recorded here.
- Historical/experimental documents are preserved and marked as superseded where applicable, not silently rewritten.
