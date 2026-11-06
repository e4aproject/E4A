# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `docs/project-status.md`: verified baseline, prioritized issue inventory, phase tracking, and maintainer decision log (the single source of truth for implementation status).
- `docs/protocol/`: home for the normative v1 protocol specification (not yet normative).

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
