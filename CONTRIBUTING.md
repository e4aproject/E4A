# 🤝 Contributing to E4A

Welcome to the **E4A (Ethos4Agents)** open-source protocol.

E4A is built as an interoperable framework aligned with open collaboration standards similar to A2A, MCP, AP2. We use semantic versioning and conventional commits.

**Start here:** [docs/project-status.md](docs/project-status.md) is the single
source of truth for what is implemented, what is broken, and what is planned.
Do not rely on older roadmap or plan documents for implementation status.

--------------------------------------------------------------------

## 🧱 Branching Model (as it actually works)

| Branch | Purpose |
|---------|---------|
| `main` | Default branch. Changes land **only via reviewed pull requests** — do not push directly. |
| Topic branches (e.g. `protocol/v1-road-to-release`, `feat/*`, `fix/*`, `docs/*`) | All work happens here and is proposed as a PR against `main`. |

There is currently **no `dev` branch**; earlier versions of this document
described one in error.

### Releases are manual

`.github/workflows/release.yml` is a **manual-only** preparation workflow
(`workflow_dispatch`): it tests, builds, and verifies the distribution
artifacts and uploads them for maintainer inspection. It never publishes.
(Earlier, this workflow published to PyPI and npm automatically on every
push to `main`; that behavior was removed in Phase 6.)

- Merging to `main` never publishes anything.
- Publishing, tagging, or deploying requires explicit maintainer approval
  and follows [docs/releasing.md](docs/releasing.md).

--------------------------------------------------------------------

## 🧪 Development workflow

1. Branch from `main`.
2. Set up the verified development environment (see `README.md` /
   `docs/quickstart.md`):
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   PYTHONPATH=sdk/python python -m pytest tests/ -q   # expect 13 passed
   ```
3. Make your change. If it changes protocol behavior, schemas, or public
   interfaces, update `docs/protocol/` (once normative), the quickstart, and
   `docs/project-status.md` in the same PR, and call out the compatibility
   impact in the PR description.
4. Run the quality tools CI runs (`flake8`, `black --check`, `mypy`,
   `bandit`) and note honestly in the PR if any gate still fails — the
   baseline status document records the known failures, so a red gate that
   predates your change should be identified as such, not hidden.
5. Open the PR against `main`. A task is "done" only when its acceptance
   criteria are met and evidence (commands, results) is recorded — link it.

## 🧩 Commit Message Format

All commits follow the [Conventional Commits](https://www.conventionalcommits.org/) specification.

## 📄 Documentation rules

- One source of truth: status claims live in `docs/project-status.md`.
- Never describe a feature as implemented because it appears in a roadmap,
  architecture, or security document. If you cannot point to code and a
  passing test, describe it as planned, partial, or deferred.
- Preserve historical documents; mark them clearly as historical or
  superseded instead of silently rewriting them.
