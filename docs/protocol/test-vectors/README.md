# E4A 1.0 test vectors

Machine-readable vectors for the E4A 1.0 specification (`../spec.md`).
A conforming implementation MUST pass all of them. The conformance suite
(TCK) is generated from these files and MUST NOT import implementation
internals to determine expected outcomes.

## Schema vectors

Each `valid-*.json` / `invalid-*.json` file contains:

- `mandate` — a mandate document (a *submission*; implementations assign
  `mandate_id`, `created_at`, and the effective `protocol_version`).
- `expect` — `"valid"` or `"invalid"` against `../mandate.schema.json`.
- `error_code` — for invalid vectors, the stable error code a submission
  MUST surface.
- `note` — why the vector exists.

## Lifecycle vectors

`lifecycle-vectors.json` contains ordered operation sequences (create,
decide, execute, get) with the expected state or error code after each step,
covering: execution without approval, approval gating, unauthorized
approvers, rejection finality, decision changes while pending, idempotent
creation and nonce conflicts, expiry, and unknown identifiers.

## Versioning

Vectors are versioned with the protocol. A vector that changes meaning
changes the protocol version; corrections that do not change meaning are
recorded in the project changelog.
