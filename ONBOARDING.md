# Onboarding to E4A
Welcome. This is a fast orientation for new contributors. Read in this order:

1. **What E4A is:** `README.md` — including the project-maturity note — and `docs/philosophy.md` for the vision behind it.
2. **What is actually true right now:** `docs/project-status.md` — the single source of truth for verified status, known breakage, and open maintainer decisions. Read this before trusting any other document's claims.
3. **Where the protocol is heading:** `ROADMAP.md` for milestones and exit criteria, and `docs/protocol/` for the v1 specification (not yet normative — the canonical mandate schema is still an open decision; `specs/` currently holds two mandate schema versions, v1 and v2).
4. **The "Hello World":** `docs/quickstart.md` — the verified, runnable path, including an explicit list of what does not work yet.
5. **Security:** `docs/security.md` — read the implementation-status table at the top before citing any mitigation.
6. **The Logic:** The Python SDK is in `sdk/python/e4a_sdk/`. The A2A bridge is in `adapters/a2a/adapter.py`. The culture: `docs/charter_manifest.md`.
7. **How to contribute:** `CONTRIBUTING.md` — branching, testing, and the release-automation warning.
