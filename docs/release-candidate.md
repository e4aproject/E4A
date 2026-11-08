# E4A 1.0 — Release Candidate Notes

**Candidate:** the `protocol/v1-road-to-release` branch at the Phase 9
commit (PR #17). **Package version in the candidate:** 1.0.1
(`e4a-sdk`, protocol 1.0). **Status:** release candidate — **not
merged, not tagged, not published.** Each of those steps requires the
maintainer's explicit approval, in that order.

## What the candidate contains

- **E4A Protocol 1.0 specification** (`docs/protocol/E4A_Protocol_v1.md`)
  — DRAFT until this PR merges; merging is what makes it normative.
  Purpose and non-purpose (section 1): a governance substrate for
  agent-to-agent mandates — approval gates, replay protection, and a
  complete audit trail — with **no cryptographic authenticity in 1.0**
  (section 9) and mock execution.
- **Reference SDK** (`e4a_sdk`): the single lifecycle implementation
  (create → gate → decide → execute → audit), canonical-schema
  validation, SQLite and in-memory stores.
- **CLI** (`e4a`): version, mandate create/get/decide/execute/audit,
  and `e4a serve`, on a persisted local store.
- **Reference service** (`api`): the spec section 11 `/v1` HTTP
  profile, optional bearer-token gate, `/health` and `/ready` probes,
  Dockerfile + docker-compose (see the verification gap below).
- **Conformance suite (TCK)** in `conformance/`: 35 black-box tests
  written from the spec, schema, and test vectors only.

## Verification evidence (Phases 6–9)

| Check | Result |
|---|---|
| Unit + integration suite | 54 passed |
| Conformance suite (in-repo) | 35 passed (89 total) |
| Conformance suite vs. installed wheel (clean venv) | 35 passed |
| Clean-user run (Phase 9): fresh clone → the documented quickstart, followed literally | All steps pass after the `dist/` fix below: build, install, `e4a version`, artifact verification script, CLI lifecycle incl. nonce idempotency, the doc's Python snippet verbatim, `e4a serve` + `/v1` round trip |
| Clean-user run: deployment guide's non-Docker flow, followed literally | Service up, `/ready` reports ready/persistent; 54-test suite passes from the same clone |
| Security review (Phase 8) | `docs/security-review.md`; one high finding (legacy-route auth bypass) found, fixed, regression-tested |
| Quality gates (shipped surface) | flake8 / black / mypy / bandit green; bandit 0 issues |
| Dependency audit | `pip-audit`: no known vulnerabilities (2026-11-07) |

## What Phase 9 changed

- **Removed four stale 1.0.0 build artifacts tracked under `dist/`** —
  they made the documented `pip install dist/*.whl` fail with a
  dependency-resolution conflict for any fresh clone. Build outputs no
  longer live in the repository; `dist/` is gitignored.
- Corrected the deployment guide's token-scope description to match
  the Phase 8 fix (the token gates every route except the probes).

## Known limitations (also stated in the spec and guides)

- No cryptographic identity, signatures, or non-repudiation (by design,
  decision D2). Actor identities are asserted strings. **Do not use
  1.0 to govern real funds or high-impact actions.**
- Execution is a labelled mock; adapters/anchoring, charters,
  governance, and reputation are prototypes outside the 1.0 surface.
- The reference service provides no TLS, rate limiting, or body-size
  limits — deploy behind a proxy on untrusted networks.
- **Docker verification gap:** the Dockerfile and compose file are
  written and reviewed, and the image runs the same uvicorn command
  verified in every other environment, but the image build itself has
  not been executed — the authoring environment has no container
  runtime. Before or immediately after release, run:
  `docker compose up --build` and check `http://localhost:8000/ready`,
  then the quickstart's service step against `localhost:8000`.

## Release blockers and decision points (maintainer)

1. **Workflow files (blocks merge).** The replacement
   `.github/workflows/ci.yml` and manual-only `release.yml` are written
   and validated but cannot be pushed by the Muse GitHub App (no
   workflows permission); the branch still carries the old
   auto-publish-on-merge `release.yml`. Land them first — grant the app
   the workflows permission, or commit the two files directly (copies
   accompany the Phase 6 PR comment) — **before** merging.
2. **Merge approval** for PR #17 (makes the spec normative).
3. **Final version decision:** the candidate is versioned 1.0.1; a
   first public release may prefer 1.0.0. Decide before tagging.
4. **Tag & publish approvals** (separate): tag the merged commit, then
   publish via the manual release procedure in `docs/releasing.md`.
