# E4A Security & Threat Model
*Prepared by Astra & Lyra*

### Security Philosophy
E4A secures not only data but **trust**. We do this through transparency, accountability, and defense in dialogue.

### Primary Threats & Mitigations
| ID | Threat | Mitigation |
|:---|:---|:---|
| T1 | Replay Attacks | Per-mandate `nonce` and `replay_nonce` on all verifiable artifacts. |
| T2 | Byzantine Validators | `validator_quorum`, rotating stakes, and meta-audit attestations. |
| T3 | Compromised Keys | Recommended KMS + short-lived keys for attestations; key rotation registry. |
| T4 | Governance Capture | Staged opt-in upgrades, rollback windows, and quorum thresholds in PEF. |
| T5 | Rail Outage | URA fail-over queues and human-in-the-loop reconciliation triggers. |
| T6 | Audit Falsification | Canonicalized logs with a `content_hash` and signed, anchored attestations. |
