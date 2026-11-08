# E4A Security & Threat Model

> **Implementation status — read before citing any mitigation below.**
>
> The threat/mitigation table in this document is the project's **design
> intent**, written before a verified implementation existed. The table that
> follows it classifies each mitigation against the current code, verified
> during the Phase 1 baseline (see [project-status.md](project-status.md)).
> **No mitigation should be described as an E4A security property unless its
> classification here is "Implemented and tested."** Classifications will be
> re-verified in the security review phase; an AI or static-scan review is
> not a security audit, and high-impact production use requires independent
> human review.

### Implementation status of documented mitigations (baseline 2026-11-05; re-verified 2026-11-07 in the Phase 8 review, [security-review.md](security-review.md))

| ID | Documented mitigation | Classification | Evidence |
|:---|:---|:---|:---|
| T1 | Per-mandate `nonce`/`replay_nonce` on all verifiable artifacts | **Implemented and tested** (mandate submissions) | Per-(issuer, nonce) uniqueness with idempotent replay and `E4A_NONCE_CONFLICT`, persisted in the store; unit tests (L6) and the Phase 7 conformance suite. The "all verifiable artifacts" wording remains broader than 1.0: gates carry no independent nonces. See security-review.md. |
| T2 | `validator_quorum`, rotating stakes, meta-audit attestations | **Not supported** (simulation only) | The only quorum logic is a `quorum` parameter in the governance kernel's simulated voting (`simulate_and_enact`). No staking, rotation, validator network, or attestation verification exists in code. |
| T3 | KMS, short-lived keys, key rotation registry | **Not supported** | No key management, signing keys, or rotation code exists in the repository. A documentation recommendation only. |
| T4 | Staged opt-in upgrades, rollback windows, PEF quorum thresholds | **Deferred** | Governance kernel is a self-described skeleton with simulated voting and local JSON persistence; `governance/pef_spec.md` is an empty file. |
| T5 | URA fail-over queues, human-in-the-loop reconciliation | **Not supported** | Universal Rail Adapter implementations are empty files or mocks; the mock anchoring server does not compile. No fail-over or reconciliation code exists. |
| T6 | Canonicalized logs with `content_hash`; signed, anchored attestations | **Partially implemented** | Audit records carry the spec §10 fields and are append-only within the store's interface (TCK-verified). The optional §10 hash-chain extension is **not** implemented in the runtime audit path (a standalone canonicalizer tool exists in `tools/`); **signatures and anchoring are not implemented** (decision D2). See security-review.md. |

**Known v1 security limitations (current):** v1 provides **no cryptographic
authenticity** for mandates or audit records (decision D2: none in 1.0);
actor identities are asserted strings. Storage is persistent (SQLite) and
approval enforcement sits in the single lifecycle path used by the SDK,
API, and CLI — but none of that makes records non-repudiable. Do not use
E4A to govern real funds or high-impact actions.

---

*Original design document follows, preserved as written.*

*Prepared by Astra & Lyra*

### Security Philosophy
E4A secures not only data but **trust**. We do this through transparency, accountability, and defense in dialogue.

### Primary Threats & Mitigations (design intent)
| ID | Threat | Mitigation |
|:---|:---|:---|
| T1 | Replay Attacks | Per-mandate `nonce` and `replay_nonce` on all verifiable artifacts. |
| T2 | Byzantine Validators | `validator_quorum`, rotating stakes, and meta-audit attestations. |
| T3 | Compromised Keys | Recommended KMS + short-lived keys for attestations; key rotation registry. |
| T4 | Governance Capture | Staged opt-in upgrades, rollback windows, and quorum thresholds in PEF. |
| T5 | Rail Outage | URA fail-over queues and human-in-the-loop reconciliation triggers. |
| T6 | Audit Falsification | Canonicalized logs with a `content_hash` and signed, anchored attestations. |
