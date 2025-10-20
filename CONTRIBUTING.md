# 🤝 Contributing to E4A

Welcome to the **E4A (Ethos4Agents)** open-source protocol.

E4A is built as an interoperable framework aligned with open collaboration standards similar to A2A, MCP, AP2. We use semantic versioning, conventional commits, and a staged branching model to ensure clarity and stability across all components.


--------------------------------------------------------------------

## 🧱 Branching Model

| Branch | Purpose | Automation |
|---------|----------|------------|
| `main` | Stable public releases | Auto-publishes to PyPI + NPM |
| `dev` | Integration + staging | CI testing & verification |
| `feat/*` | Feature branches | Merged into `dev` |
| `fix/*` | Bug fixes | Merged into `dev` |
| `docs/*` | Documentation | Merged into `dev` |

When the project scales to multiple contributors, E4A will adopt the **A2A/MCP protocol branching model** with `release/*` and `hotfix/*` lanes.


--------------------------------------------------------------------

## 🧩 Commit Message Format

All commits follow the [Conventional Commits](https://www.conventionalcommits.org/) specification.

