# E4A Protocol Specification

**Status: NOT YET NORMATIVE.**

This directory will hold the normative v1 protocol specification: the
canonical mandate schema and protocol version, the mandate lifecycle state
machine, error codes, identifier/timestamp/expiry rules, idempotency and
replay behavior, approval policy, audit event requirements, compatibility and
schema-evolution rules, and the cryptographic-signature decision.

Until the v1 scope-lock phase is complete and the maintainer has approved the
decisions recorded in [../project-status.md](../project-status.md) (D1–D4),
nothing here — and nothing in `specs/`, the architecture documents, or the
SDK's current behavior — should be treated as the normative protocol. In
particular:

- `specs/` currently contains **two** mandate schemas (`mandate_v1.json` and
  `mandate_v2.json`); which one is canonical is undecided (decision D1).
- Current SDK behavior is a Phase 1 prototype and may diverge from the locked
  spec; divergences will be recorded in the project status document, not
  silently treated as specification.

When the specification is locked, this file will link each normative document
and the versioned test vectors that accompany it, and a separately written
implementation must be able to conform using only these documents.
