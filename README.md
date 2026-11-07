# Ethos4Agents (E4A) Protocol

**An open protocol for organizational culture among multi-agent systems.**

E4A enables multi-agent systems to express, share, and enforce organizational culture, governance primitives, and safety invariants while interoperating across diverse runtimes and administrative domains. It complements existing standards like A2A and AP2 by adding a focused layer for culture, governance, and auditability.

**Purpose and non-purpose of v1:** E4A is intended to become a cultural norm by which AI agents interact and form their own societies. Version 1.0 is not that full cultural protocol; it is the governance substrate—a constitutional kernel providing explicit intent, mandates, approval gates, lifecycle rules, and auditable records. Charter adoption, membership and constellation formation, norm evolution, reflection and repair, reputation consequences, and federation remain future cultural-layer work.

> **Project maturity — read this first**
>
> E4A is an **early-stage prototype**, not a production protocol and not yet a
> working v1 release. A verified baseline (what actually runs, what is broken,
> and what is only documented) is maintained in
> [docs/project-status.md](docs/project-status.md), which is the single source
> of truth for implementation status. In short, as of the last verification:
>
> - The Python SDK implements the protocol 1.0 mandate lifecycle
>   (create → validate against the one canonical schema → approval gates →
>   mock-execute → audit trail) with SQLite persistence and a `/v1` HTTP
>   reference service; **49 tests** pass from a plain checkout.
> - The **built artifact installs and runs in a clean environment**:
>   wheel and sdist include the SDK with its bundled canonical schemas,
>   the `e4a` CLI, and the service package; a clean-venv install passes
>   import, CLI, service, and lifecycle verification. The package is
>   **not yet published** to PyPI.
> - One canonical mandate schema is locked (decision D1: the v2 lineage,
>   published as `docs/protocol/mandate.schema.json`); 1.0 has **no
>   cryptographic identity** — actor identifiers are asserted (decision
>   D2) — and must not govern real funds.
> - Governance, validator, and cross-rail components are skeletons, mocks,
>   or empty modules, and are outside the v1 release surface. Security
>   properties described in the docs are design intentions unless the
>   status document records them as implemented and tested.
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

## Getting Started

Build and install the artifact from a clone (the package is not yet on
PyPI). The full verified path is the [Quickstart](docs/quickstart.md);
in short:

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

2.  **Create a virtual environment, build, and install the artifact:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install build
    python -m build
    pip install dist/*.whl
    e4a version
    ```

3.  **Run the tests** (from the checkout):
    ```bash
    pip install -r requirements.txt
    python -m pytest tests/ -q
    ```
    Expected result at the last verification: **49 passed**.

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

As of Phase 6, the flake8, black, mypy, and bandit gates pass over the
shipped code (SDK, CLI, API, tests, scripts) and CI also builds and
verifies the distribution artifact. Legacy prototype directories are
excluded from the gates until they are repaired or retired. Do not treat
a green badge claim anywhere as evidence; check the status document.

## Publishing

Releases are **manual and maintainer-approved**; nothing publishes
automatically. `pyproject.toml` is the canonical Python packaging
metadata; the npm package (`@e4aproject/protocol`) is a thin wrapper,
version-aligned with the Python package. See
[docs/releasing.md](docs/releasing.md) for the release procedure.
