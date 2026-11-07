# The Ethos4Agents (E4A) Protocol Roadmap

**Status:** Active — strategic direction only.
**Last updated:** 2026-11-05

This roadmap states milestones and their **exit criteria**. It does not certify
completion: verified implementation status lives in
[docs/project-status.md](docs/project-status.md), which governs whenever the
two disagree. Progress is measured by exit criteria being met with recorded
evidence, not by dates.

## Current milestone: v1 reference implementation

**Goal:** one complete, testable mandate lifecycle that a new contributor can
install, run, and verify — create a mandate, validate it against one canonical
schema, enforce required approvals, execute (mock execution clearly labelled),
and produce an auditable record.

**Exit criteria:**

- Canonical protocol/schema version locked and specified in
  `docs/protocol/`, with positive and negative test vectors.
- Reference SDK enforces the lifecycle on every execution path; no path
  bypasses validation or a required approval.
- A clean environment can install the **built artifact** (not just a checkout)
  and complete the quickstart.
- An independent conformance suite (TCK) validates protocol behavior from the
  spec and test vectors without importing implementation internals.
- Every security property in `docs/security.md` is classified as implemented
  and tested, partially implemented, extension point, deferred, or not
  supported — with evidence.
- Release candidate prepared and approved by the maintainer before anything is
  published, tagged, or deployed.

## Later milestones (not v1)

- **Interoperability:** A2A/AP2 adapter conformance against the locked v1
  spec; a Technology Compatibility Kit release for third-party implementers.
- **Deployment hardening:** documented production deployment profile,
  independent security review, operational runbooks.
- **Ecosystem:** documentation site, partnerships, developer tooling.
- **Learning layer (vision):** formalized `WisdomArtifact` schema, reference
  Weaver agent, scholarly ledger prototype — all deferred until the v1
  lifecycle is proven.

## History

Earlier versions of this roadmap (through 2025-11-01) described a **Genesis
Sprint**, **Phase 1.5 "The Bridge"** (architectural/philosophical foundation —
documents and repository restructure, recorded as complete at that time),
**Phase 2 "The Forge"**, **Phase 3 "The Embassy"**, and **Phase 4 "The
Academy"**. Those phase names are retired. Their artifacts remain in the
repository as historical and design material; claims in them about
implementation completeness were superseded by the verified baseline in
[docs/project-status.md](docs/project-status.md) (November 2026).
`plans/E4A_v1.1.yml` is likewise historical — see the header in that file.
