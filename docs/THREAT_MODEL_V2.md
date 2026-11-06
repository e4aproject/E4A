# E4A Threat Model v2: Inter-Protocol Era

> **Status note (2026-11-05):** This is a **design-stage** threat model. The
> mitigations below (Treaty Tokens, Charter hash validation, bridge schema
> pipelines) are proposals, not implemented controls, unless the
> implementation-status table in [security.md](security.md) records them as
> implemented and tested. Verified status lives in
> [project-status.md](project-status.md).

This document extends the Phase 1 security model to account for risks from diplomatic expansion.

| Threat | Mitigation |
|:---|:---|
| **Treaty Spoofing** | Use short-lived, dual-signature Treaty Tokens for diplomatic sessions. |
| **Cultural Drift** | Enforce guardrails via immutable Charter hash validation in all attestations. |
| **Bridge Poisoning** | Implement a strict schema verification pipeline in the A2A adapter. |
| **Governance Capture**| Weight quorum attestation votes by reputation score and role. |
