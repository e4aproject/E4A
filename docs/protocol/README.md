# E4A Protocol Specification

**Status: DRAFT 1.0 — locked for implementation on the road-to-release
branch, pending maintainer approval of the introducing pull request.**

- [spec.md](spec.md) — the normative specification: scope, mandate object,
  lifecycle state machine, expiry, idempotency/replay, approval gates,
  security limitations, audit records, API profile, persistence and
  compatibility rules, and error codes.
- [mandate.schema.json](mandate.schema.json) — the canonical mandate schema
  (`$id`: `https://e4aproject.github.io/E4A/schemas/mandate-1.0.json`).
- [test-vectors/](test-vectors/) — machine-readable schema and lifecycle
  vectors a conforming implementation must pass.

## Decisions this draft embodies

Recorded in [../project-status.md](../project-status.md) and approved by the
maintainer on 2026-11-05:

- **D1 — Canonical schema:** the former `specs/mandate_v2.json` (mandate with
  a required structured `intent`) is canonical for protocol 1.0, with
  explicit versioning, optional `expires_at`, and closed objects. The
  prototype schemas in `specs/` are superseded for protocol purposes.
- **D2 — Signatures:** **not in 1.0.** The specification states plainly that
  1.0 provides no cryptographic authenticity (spec §9) rather than implying
  otherwise. `attestations` is reserved for a future extension.
- **D3 — Persistence:** a store interface with two backends — embedded
  SQLite for the reference deployment, in-memory for tests (spec §12).
- **D4 — API scope:** a minimal versioned HTTP API over the mandate
  lifecycle is part of 1.0 as the interoperability demonstration (spec §11).

Where the current prototype code disagrees with the specification, the
divergences are enumerated in spec §13 and tracked in the project status
document for the implementation phase. Approval of the pull request makes
this draft the normative 1.0 specification; amendments after that point
follow the compatibility rules in spec §12.
