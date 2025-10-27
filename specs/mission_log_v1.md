# Mission Log v1 - Canonicalization & Anchoring
## Purpose
This document defines the deterministic serialization and hashing process for `mission_log` entries. This ensures that signatures and cross-rail anchors are verifiable across different runtimes, languages, and platforms.

## Canonicalization Rules
1.  **Serialization:** UTF-8 JSON, no insignificant whitespace, keys sorted lexicographically at each object level.
2.  **Date-time:** RFC3339, always in UTC (e.g., `2025-10-25T19:00:00Z`).
3.  **Hash Algorithm:** SHA-256, with the digest encoded as a lowercase hexadecimal string.

## Log Entry Types
The log supports various entry types, including `mandate_created`, `mandate_executed`, `meta_audit`, and the crucial **`reflection_event`**, which captures learning from mistakes.

## Anchoring Process
To produce a verifiable anchor, an agent MUST:
1.  Construct the full log entry payload.
2.  Canonicalize the payload according to the rules above.
3.  Compute the SHA-256 hash to generate the `content_hash`.
4.  Store this `content_hash` in the entry, which is then signed.
