# Ethos4Agents (E4A) Protocol

**An open protocol for organizational culture among multi-agent systems.**

E4A enables multi-agent systems to express, share, and enforce organizational culture, governance primitives, and safety invariants while interoperating across diverse runtimes and administrative domains. It complements existing standards like A2A and AP2 by adding a focused layer for culture, governance, and auditability.

> **Project maturity — read this first**
>
> E4A is an **early-stage prototype**, not a production protocol and not yet a
> working v1 release. A verified baseline (what actually runs, what is broken,
> and what is only documented) is maintained in
> [docs/project-status.md](docs/project-status.md), which is the single source
> of truth for implementation status. In short, as of the last verification:
>
> - The Python SDK source works from a repository checkout for a minimal
>   mandate flow (create → validate → mock-execute → local audit log), and its
>   13 tests pass when the package path is supplied (see below).
> - The **packaged install is currently broken**: the built wheel cannot be
>   imported in a clean environment and its `e4a` CLI entry point is missing
>   from the distribution. Repair is tracked in the project status document.
> - There are **two mandate schema versions** in `specs/` (v1 and v2) and code
>   paths disagree about which is canonical. Choosing one is a pending
>   maintainer decision (see the status document, decision D1).
> - Governance, validator, and cross-rail components are skeletons, mocks, or
>   empty modules. Security properties described in the docs are design
>   intentions unless the status document records them as implemented and
>   tested.
>
> **Non-goals for v1:** validator staking/quorums, multi-rail settlement,
> blockchain anchoring, privacy-preserving learning, and production A2A/AP2
> integrations are deferred and are not part of the v1 critical path.

## Why E4A?

As multi-agent systems become the norm, cultural alignment and accountable governance are critical for reliable coordination at scale. E4A exists to:
-   **Establish Norms:** Ground multi-agent systems in a consistent set of organizational norms.
-   **Enable Collaboration:** Make culture and governance first-class artifacts that agents can reason about.
-   **Promote Open Standards:** Extend A2A and AP2 with auditable cultural primitives.
-   **Ensure Accountability:** Maintain transparency through signed mandates and audit trails.
-   **Reduce Risk:** Enforce human-in-the-loop gates and safety thresholds.
-   **Accelerate Impact:** Provide reusable constructs that map to well-tested organizational theories.

## Getting Started (development, from a source checkout)

The packaged install does not work yet (see the maturity note above). The
verified way to run E4A today is from a clone:

### Prerequisites

-   Python 3.10+
-   pip
-   Git

### Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/e4aproject/E4A.git
    cd E4A
    ```

2.  **Create a virtual environment and install the dependencies:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Run the tests** (the SDK package lives under `sdk/python`, so its path
    must be supplied until packaging is repaired):
    ```bash
    PYTHONPATH=sdk/python python -m pytest tests/ -q
    ```
    Expected result at the last verification: **13 passed**.

## Quick Start

The quickest way to see E4A in action is to follow the [Quickstart Guide](docs/quickstart.md), which walks through creating, validating, and (mock-)executing a mandate using the flow above. Every step in the quickstart is verified against the current code; steps that do not work yet are marked as such there rather than presented as working.

## Documentation map

- [docs/project-status.md](docs/project-status.md) — **authoritative** verified status, blockers, and decisions.
- [ROADMAP.md](ROADMAP.md) — strategic milestones and exit criteria.
- [docs/protocol/](docs/protocol/) — the normative v1 protocol specification (being locked; not yet normative).
- [docs/quickstart.md](docs/quickstart.md) — verified runnable path.
- [docs/security.md](docs/security.md) — threat model with an implementation-status classification for each control.
- [CONTRIBUTING.md](CONTRIBUTING.md) — development workflow and release rules.
- Historical and design documents (e.g. `docs/philosophy.md`,
  `docs/E4A_Level2.1_Validated.md`, `plans/`) describe intent and history;
  where they conflict with the status document, the status document governs.

## Code Quality

This project uses a suite of tools intended to enforce code quality standards, configured in `.github/workflows/ci.yml`:

-   **Linting:** `flake8` is used to check for style and logical errors.
-   **Formatting:** `black` is used to ensure a consistent code style.
-   **Type Checking:** `mypy` is used to check for type errors.
-   **Security:** `bandit` is used to scan for common security vulnerabilities.
-   **Testing:** `pytest` is used to run the test suite, and `coverage.py` is used to measure test coverage.

Note: at the last verification the codebase did **not** pass the flake8/black
gates (see the status document). Do not treat a green badge claim anywhere as
evidence; check the status document.

## Publishing

This repository uses `pyproject.toml` as the canonical Python packaging metadata source. The npm package is scoped under `@e4aproject` and is configured to publish publicly. **Do not rely on any published artifact until the status document records a verified release process** — see [docs/PUBLISHING.md](docs/PUBLISHING.md) and the release-engineering phase in the status document.
