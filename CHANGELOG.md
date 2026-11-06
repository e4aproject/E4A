# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `docs/project-status.md`: verified baseline, prioritized issue inventory, phase tracking, and maintainer decision log (the single source of truth for implementation status).
- `docs/protocol/`: home for the normative v1 protocol specification (not yet normative).

### Added (SDK repair, Phase 4)
- `e4a_sdk/errors.py`: stable protocol error codes (`E4A_*`) carried on exceptions; `e4a_sdk/store.py`: persistence interface with in-memory and SQLite backends; `e4a_sdk/schemas/`: canonical schemas bundled inside the package (the package now imports and runs standalone, outside the repo tree); root `conftest.py` so the documented test command works from a checkout; `tests/test_protocol_vectors.py` (schema vectors via engine + direct, lifecycle L1–L8, audit, restart persistence, adapter alignment).
- Mandate engine rewritten to the 1.0 lifecycle: explicit stored state machine, approval gates created at submission, per-(issuer, `replay_nonce`) idempotency with `E4A_NONCE_CONFLICT`, mandate/gate expiry as a distinct `expired` state, spec-shaped audit events with `mock: true` on execution.
- A2A adapter no longer pre-validates against the retired v1 schema — one canonical validation path in the engine.

### Changed (Phase 4)
- All `sdk.python.e4a_sdk.*` imports unified to `e4a_sdk.*` (api, adapters, tests, engine demo). Gate schema enum extended with `expired`. Three gate-integration tests rewritten: they encoded the prototype's lazy gate creation and error-message parsing, which the 1.0 spec abolishes.

### Added (protocol draft)
- Draft E4A protocol specification 1.0 (`docs/protocol/spec.md`) with the canonical mandate schema (`docs/protocol/mandate.schema.json`, derived from `specs/mandate_v2.json` per decision D1) and machine-readable test vectors (9 schema vectors, 8 lifecycle vectors). Maintainer decisions D1–D4 recorded in `docs/project-status.md`: canonical schema = v2 lineage; no cryptographic signatures in 1.0; SQLite + in-memory persistence backends; minimal versioned API in scope. **The draft becomes normative on maintainer approval of its pull request.**

### Changed
- Documentation system reconciled: README, ROADMAP, quickstart, security, CONTRIBUTING, and ONBOARDING now distinguish verified behavior from design intent, mark deferred functionality as deferred, and no longer present the broken packaged install or the un-runnable adapter/anchoring flows as working.
- ROADMAP rewritten around milestones with exit criteria; earlier phase names (Genesis Sprint, The Bridge, The Forge, The Embassy, The Academy) retired to a history section.

### Notes
- No functional code changes. The entries above are documentation-only and are **not** a release; nothing has been published or tagged.

## [1.0.1] - 2025-11-09

### Fixed
- Fixed failing tests in `tests/test_gate_engine.py`.
- Addressed deprecation warnings by replacing `datetime.utcnow()` with `datetime.now(UTC)`.

### Added
- Added `__all__` to `sdk/python/e4a_sdk/__init__.py`.

### Changed
- Bumped version to `1.0.1`.
