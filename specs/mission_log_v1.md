# Mission Log v1 - Canonicalization & Anchoring
## Purpose
This document defines the deterministic serialization and hashing process for `mission_log` entries to ensure signatures and anchors are verifiable across runtimes.

## Canonicalization Rules
1.  **Serialization:** UTF-8 JSON, no insignificant whitespace, keys sorted lexicographically.
2.  **Date-time:** RFC3339, always in UTC (e.g., `2025-10-25T19:00:00Z`).
3.  **Hash Algorithm:** SHA-256, with the digest encoded as a lowercase hexadecimal string.

## Core Entry Types
The mission log is built around several key entry types, including:
- **`mandate_created`**: The initiation of a new task.
- **`mandate_executed`**: The completion of a task.
- **`meta_audit`**: A validator's summary of network health.
- **`reflection_event`**: An agent's self-acknowledged correction of a mistake, forming the basis of the Growth Mindset.
