# E4A Protocol Specification — Version 1.0 (DRAFT)

**Status:** Draft locked for implementation on the v1 road-to-release branch,
pending maintainer review of the pull request that introduces it. When that
review is approved, this document and `mandate.schema.json` become the
normative E4A 1.0 specification. Until then, where this specification and the
current code disagree, the disagreement is a defect in the code (to be fixed
in the implementation phase) or an error in this draft (to be fixed by
amendment) — it is never silently resolved in favor of current behavior.
Known divergences are listed in §13.

The key words **MUST**, **MUST NOT**, **SHOULD**, and **MAY** are to be
interpreted as in RFC 2119.

---

## 1. Scope

### Purpose and non-purpose

E4A is intended to become a cultural norm by which AI agents interact and
form their own societies. **Version 1.0 is not that full cultural protocol.**
It is the governance substrate for that larger purpose: a constitutional
kernel that makes commitments legible, reviewable, and auditable.

Version 1.0 provides explicit intent as a first-class artifact, the mandate
lifecycle, approval gates, lifecycle rules, and audit records. It does not
yet specify, at protocol level:

- charter adoption or amendment;
- membership, joining or leaving, role assignment, or constellation
  formation;
- a norm lifecycle of proposal, contestation, adoption, sanction, repair,
  and sunset;
- Reflection Events or Wisdom Artifacts;
- reputation consequences; or
- inter-group diplomacy or federation.

Those capabilities form the cultural and society layer that follows 1.0.
Describing 1.0 itself as the complete cultural protocol would therefore be
an overclaim. In addition, because 1.0 provides no cryptographic
authenticity and its reference execution is simulated, 1.0 must not be used
to govern real funds (see §9).

The design draws on organizational theory: delegation and principal–agent
theory; institutional theory; Ostrom-style commons governance;
organizational learning; role theory, expressed in E4A as “roles, not
ranks”; and trust and reputation. This version names those roots but does
not yet formally cite them or test whether using the protocol produces the
behaviors the theories predict. Making that mapping—and its evaluation—
explicit is future work.

### Specified scope

E4A 1.0 specifies the **mandate lifecycle**: how a mandate is created,
validated, approved or rejected, executed, and audited, in a way that
independent implementations can interoperate on.

Explicitly **out of scope** for 1.0 (deferred, and conforming implementations
MUST NOT require them): validator networks, staking, or quorums; multi-rail
or blockchain settlement and anchoring; cryptographic signatures and
attestations (see §9); privacy-preserving learning; distributed governance;
production A2A/AP2 integrations (adapters are non-normative examples).

## 2. Protocol version and identifiers

- The protocol version is the string `"1.0"`. The canonical mandate schema is
  `mandate.schema.json` in this directory, identified by its `$id`.
- A mandate MAY carry `protocol_version`; absence means `"1.0"`.
  Implementations MUST store the effective version on the record and return
  it on retrieval. A submission naming an unsupported version MUST be
  rejected with `E4A_UNSUPPORTED_VERSION`.
- `mandate_id` is an opaque string, unique within an implementation. If a
  submission omits it, the implementation MUST assign one (UUID4 in the
  reference implementation) before storing.
- Actor identifiers (`issuer`, `beneficiary`, approvers) are strings,
  conventionally DID-shaped. In 1.0 they are **asserted, not verified**
  (see §9).

## 3. The mandate object

A mandate is a JSON object validated by the canonical schema. Submission
requires `issuer`, `beneficiary`, and `intent`. A stored record additionally
carries `mandate_id`, `created_at`, and the effective `protocol_version`.

- `intent` is a required object with required string fields `goal`,
  `expected_outcome`, `contextual_tone`, and `statistical_purpose`, plus an
  optional `requires_approval` array of actor identifiers.
- Objects are **closed**: unknown properties at the top level or inside
  `intent` MUST be rejected with `E4A_VALIDATION_FAILED`.
- `amount`/`currency` are record-keeping only in 1.0. Execution in 1.0 is
  mock execution (§7); no value moves.
- Field limits: implementations SHOULD accept mandates up to 64 KiB
  serialized; larger submissions MAY be rejected with
  `E4A_VALIDATION_FAILED`.

## 4. Lifecycle

States: `created`, `pending_approval`, `approved`, `executed`, `rejected`,
`expired`, `failed`. (`approved` is transient for mandates whose gate
resolves before execution is requested.)

| From | Event | To | Notes |
|---|---|---|---|
| — | submit valid mandate, no approval required | `created` | Audit: `mandate_created` |
| — | submit valid mandate, `requires_approval` non-empty | `pending_approval` | A gate is created **at submission time** with the listed approvers. Audit: `mandate_created`, `gate_created` |
| `created` | execute | `executed` | §7 preconditions. Audit: `mandate_executed` |
| `pending_approval` | all required approvers approve | `approved` | Gate resolves approved. Audit: `gate_approved` |
| `pending_approval` | any required approver rejects | `rejected` | Terminal. Audit: `gate_rejected` |
| `pending_approval` | gate expiry passes | `expired` | Terminal. Audit: `gate_expired` |
| `created` or `approved` | expiry (`expires_at`) passes before execution | `expired` | Terminal |
| `approved` | execute | `executed` | Audit: `mandate_executed` |
| `created` or `approved` | executor reports failure | `failed` | Terminal. Audit: `mandate_failed` |

Rules:

- **No other transitions are permitted.** Any operation that would cause one
  MUST fail with `E4A_INVALID_TRANSITION` and MUST NOT change state.
- Terminal states (`executed`, `rejected`, `expired`, `failed`) are final; a
  mandate is executed **at most once**.
- An approval or rejection decision MAY be changed by the same actor while
  the gate is still `pending_approval`; the change is audited
  (`approval_recorded` / `rejection_recorded` per decision, including
  changes).

## 5. Expiry

- A mandate MAY carry `expires_at` (RFC 3339).
- A gate created for a mandate MUST have its own expiry; if the mandate has
  `expires_at`, the gate expiry MUST NOT be later than it. Gate expiry is a
  distinct event from rejection and MUST produce state `expired`, not
  `rejected`.
- An expired mandate or gate MUST NOT transition further, except that
  retrieval MUST continue to work.

## 6. Idempotency and replay

- A submission MAY carry `replay_nonce`. The pair (`issuer`, `replay_nonce`)
  MUST be unique per implementation.
- A duplicate submission with the same (`issuer`, `replay_nonce`) and an
  identical mandate body MUST return the original stored record, MUST NOT
  create a second mandate, and MUST NOT emit a second `mandate_created`
  audit event. Responses SHOULD indicate the replay (e.g. an
  `idempotent_replay: true` marker out-of-band or an HTTP 200 vs 201
  distinction in the API profile, §11).
- A duplicate `replay_nonce` from the same issuer with a **different** body
  MUST be rejected with `E4A_NONCE_CONFLICT`.
- Submissions without a `replay_nonce` have no idempotency guarantee; each
  creates a new mandate.

## 7. Execution

An implementation MUST execute a mandate only when **all** hold:

1. The mandate exists and is in state `created` or `approved`.
2. It is not expired (§5).
3. If approval is required, its gate has resolved `approved` (§8).

Otherwise execution MUST fail without side effects, with
`E4A_APPROVAL_REQUIRED` (gate still pending or absent),
`E4A_MANDATE_REJECTED`, `E4A_MANDATE_EXPIRED`, or
`E4A_INVALID_TRANSITION` (already executed/failed), as applicable.

Execution in 1.0 is **mock execution**: the implementation records the
execution, computes any fee split from `fee_distribution` as record-keeping,
and emits the audit event. Mock execution MUST be unmistakably identified as
mock in APIs, logs, and examples; it MUST NOT be presented as settlement,
anchoring, or any external side effect.

## 8. Approval gates

- When `intent.requires_approval` is present and non-empty, submission
  creates exactly one gate naming those actors as required approvers.
- **Authorization:** only a listed required approver may approve or reject.
  A decision from any other actor MUST fail with
  `E4A_UNAUTHORIZED_APPROVER` and MUST NOT change state.
- **Resolution:** the gate resolves `approved` when **all** required
  approvers have approved; it resolves `rejected` as soon as **any** required
  approver rejects; it resolves `expired` at its expiry. A resolved gate is
  final.
- The issuer MAY be listed as an approver, but a mandate with
  `requires_approval` MUST list at least one approver other than the issuer
  if the deployment's policy requires independent approval — this is a
  deployment policy decision, out of protocol scope for 1.0, and MUST be
  documented by the deployment when relied upon.

## 9. Security properties and limitations (normative honesty)

- **E4A 1.0 provides no cryptographic authenticity.** Mandates, approvals,
  and audit records are not signed. Actor identifiers are asserted strings;
  1.0 defines no enrollment, key, or trust-lookup mechanism.
- Authorization in 1.0 is exactly §8's membership rule. Deployments MUST NOT
  represent 1.0 approval as non-repudiable.
- Audit records (§10) are integrity-**evident** only if the deployment adds
  the optional hash chaining described there; plain storage provides no
  tamper evidence.
- Consequently, 1.0 MUST NOT be used to govern real funds, irreversible
  actions, or high-impact operations. A future version may add signatures;
  the field name `attestations` is reserved for that extension, and 1.0
  implementations MUST reject it as unknown (§3) rather than silently
  accepting it.

## 10. Audit records

For every lifecycle event in §4 the implementation MUST append an audit
record containing at least: `entry_type` (event name), `mandate_id`,
`timestamp` (RFC 3339, UTC), and the event's salient payload:

| Event | Required payload |
|---|---|
| `mandate_created` | the stored mandate |
| `gate_created` | `gate_id`, `required_approvers`, gate `expires_at` (or null) |
| `approval_recorded` / `rejection_recorded` | `gate_id`, actor, resulting gate tally |
| `gate_approved` / `gate_rejected` / `gate_expired` | `gate_id`, final tally or expiry |
| `mandate_executed` | executor identifier, execution result, `mock: true` |
| `mandate_failed` | executor identifier, failure detail |

Audit records MUST be append-only within the implementation's store and
retrievable by `mandate_id`. **Optional integrity extension:** a record MAY
carry `prev_hash` and `content_hash` (SHA-256 over the canonical JSON of the
record without `content_hash`, chained to the previous record's
`content_hash`). Deployments claiming tamper evidence MUST implement this
extension; the base protocol does not claim it.

## 11. API profile (reference service)

Where an HTTP API is offered (per decision D4, the reference service),
endpoints are versioned under `/v1`:

| Operation | Method & path | Success | Principal errors |
|---|---|---|---|
| Create mandate | `POST /v1/mandates` | 201, stored record | `E4A_VALIDATION_FAILED` (400), `E4A_NONCE_CONFLICT` (409), `E4A_UNSUPPORTED_VERSION` (400) |
| Retrieve mandate | `GET /v1/mandates/{id}` | 200, stored record | `E4A_NOT_FOUND` (404) |
| Record decision | `POST /v1/mandates/{id}/decisions` with `{actor, decision: "approve"|"reject"}` | 200, gate state | `E4A_NOT_FOUND` (404), `E4A_UNAUTHORIZED_APPROVER` (403), `E4A_INVALID_TRANSITION` (409) |
| Execute mandate | `POST /v1/mandates/{id}/execute` | 200, execution result | `E4A_NOT_FOUND` (404), `E4A_APPROVAL_REQUIRED` (409), `E4A_MANDATE_REJECTED` (409), `E4A_MANDATE_EXPIRED` (409), `E4A_INVALID_TRANSITION` (409) |
| Retrieve audit | `GET /v1/mandates/{id}/audit` | 200, array of audit records | `E4A_NOT_FOUND` (404) |

Errors are returned as a JSON envelope:
`{"error": {"code": "<stable code>", "message": "<human-readable detail>"}}`.
The `code` is normative; `message` text is not, and clients MUST NOT parse
it. (This replaces the prototype's pattern of encoding state in exception
strings.)

API authentication is deployment-defined in 1.0 and MUST be documented by
the deployment; the protocol defines authorization semantics (§8) once an
actor identity is established. An API MUST NOT silently treat an
unauthenticated caller as an approver.

## 12. Persistence and compatibility

- Implementations MUST define a store interface separating the lifecycle
  logic from storage (per decision D3, the reference implementation ships an
  embedded SQLite backend for the reference deployment and an in-memory
  backend for tests).
- Persisted records MUST carry `protocol_version`. A store containing a
  newer major version than the implementation supports MUST fail loudly with
  `E4A_STORE_VERSION`, never silently mis-read.
- **Compatibility:** within 1.x, changes to the canonical schema MUST be
  additive-optional only (new optional fields, never new required fields,
  never narrower types). Breaking changes require a new major protocol
  version and a new schema `$id`. Records written under `specs/` v1 or v2
  prototype schemas are pre-1.0 artifacts; implementations MAY import them
  but MUST re-validate against the canonical schema and report failures
  rather than coercing silently.
- The prototype schemas in `specs/` are superseded by
  `docs/protocol/mandate.schema.json` for protocol purposes; they remain in
  the repository as history.

## 13. Known divergences: current prototype vs. this specification

Recorded so the implementation phase can close them one by one; each maps to
the issue inventory in [../project-status.md](../project-status.md).

1. The engine validates against `specs/mandate_v2.json` while the A2A adapter
   validates against `specs/mandate_v1.json` (no `intent`). → One canonical
   validation path (§3).
2. Schemas are loaded from outside the package and the installed artifact is
   unusable. → Schema ships with the implementation (§12, packaging phase).
3. The engine creates a gate lazily during a failed `execute` call, as a side
   effect of an error. → Gates are created at submission (§4, §8).
4. Gate expiry is recorded as `rejected`. → Distinct `expired` state (§5).
5. Errors are free-text exception messages (including embedding gate IDs in
   strings). → Stable error codes (§11).
6. No mandate state field is stored; "executed" lives only in the result
   object, so double-execution is not prevented. → Explicit state machine
   (§4).
7. `replay_nonce` uniqueness is a global in-memory scan, not per-issuer, and
   conflicting reuse is silently accepted. → §6 semantics.
8. Approval is only consulted on the engine's execute path; other paths
   (API/CLI/adapter) do not share one enforcement point. → Single lifecycle
   service in the implementation phase.
9. Audit records exist (scribe JSONL) but lack the `timestamp` field name
   and `mock: true` marker this spec requires. → §10 alignment.

## 14. Error code summary

| Code | Meaning |
|---|---|
| `E4A_VALIDATION_FAILED` | Submission does not conform to the canonical schema |
| `E4A_UNSUPPORTED_VERSION` | Unknown `protocol_version` |
| `E4A_NOT_FOUND` | No mandate (or gate) with that identifier |
| `E4A_UNAUTHORIZED_APPROVER` | Actor is not a required approver for the gate |
| `E4A_APPROVAL_REQUIRED` | Execution attempted before gate approval |
| `E4A_MANDATE_REJECTED` | Execution attempted on a rejected mandate |
| `E4A_MANDATE_EXPIRED` | Execution attempted after expiry |
| `E4A_INVALID_TRANSITION` | Operation not permitted in the current state |
| `E4A_NONCE_CONFLICT` | `replay_nonce` reused with a different mandate body |
| `E4A_EXECUTION_FAILED` | Executor failed; mandate is in state `failed` |
| `E4A_STORE_VERSION` | Persisted data version is unsupported |

## 15. Test vectors

`test-vectors/` in this directory contains machine-readable vectors:
schema vectors (documents that MUST validate or MUST fail against
`mandate.schema.json`, with the expected error code) and lifecycle vectors
(ordered operation sequences with expected outcomes and error codes). A
conforming implementation MUST pass all of them; the conformance suite
(TCK) is built from these vectors without importing implementation
internals.
