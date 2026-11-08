# Deploying the E4A 1.0 reference service

The reference service is a small FastAPI application (`api/server.py`)
implementing the protocol 1.0 API profile (spec §11) on top of the SDK's
lifecycle engine, with SQLite persistence.

> **Security posture — read first.** E4A 1.0 provides **no cryptographic
> authenticity** (spec §9). Actor identities are asserted, and the optional
> API token below is a shared-secret gate, not authentication of actors.
> Run this service on a trusted network or behind a real authentication
> layer. Do not use it to govern real funds or high-impact actions.
The service itself provides no TLS, rate limiting, or request-size
limits; on any network you do not fully trust, terminate TLS and set
those limits at a reverse proxy in front of it (the bearer token is
sniffable over plain HTTP). See `docs/security-review.md` (Phase 8).

## Run with Docker (reference local deployment)

```bash
docker compose up --build
# service on http://localhost:8000 — check http://localhost:8000/ready
```

Data persists in the `e4a-data` volume (SQLite file at `/data/e4a-v1.db`).
Set a token before exposing the port beyond your machine:

```bash
E4A_API_TOKEN='choose-a-long-random-value' docker compose up --build
```

## Run without Docker

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=.:sdk/python E4A_DB_PATH=./data/e4a-v1.db \
  uvicorn api.server:create_app --factory --host 0.0.0.0 --port 8000
```

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `E4A_DB_PATH` | `./data/e4a-v1.db` | SQLite database file. The directory is created if missing. `:memory:` selects an ephemeral in-memory store (development only; the service logs a warning, and `/ready` reports `"persistent": false`). |
| `E4A_API_TOKEN` | *(unset)* | If set (non-empty), every `/v1` request requires `Authorization: Bearer <token>`. `/health` and `/ready` stay open for orchestrator probes. |

Invalid configuration fails at startup (for example, a database written by
an unsupported newer protocol major version raises `E4A_STORE_VERSION`
rather than starting with mis-read data).

## Health and readiness

- `GET /health` — liveness: the process is up.
- `GET /ready` — readiness: the store answers; reports the protocol version,
  whether storage is persistent, and whether the token gate is on. Returns
  503 if the store is unavailable.

## Persistence, backup, restore

- All state (mandates, gates, lifecycle states, audit records) lives in the
  single SQLite file at `E4A_DB_PATH`. Restarting the service preserves
  mandates, pending gates, and audit trails exactly (covered by automated
  restart tests and verified manually against a live server).
- **Backup:** stop the service (or use SQLite's online backup) and copy the
  database file. **Restore:** put the file back at `E4A_DB_PATH` and start.
- The governance prototype additionally writes
  `sdk/python/data/governance_state.json`; it is legacy prototype state, not
  part of the 1.0 protocol data.

## Upgrades

- Protocol compatibility is additive-only within 1.x (spec §12). Upgrading
  the service within 1.x requires no data migration.
- A database stamped with a newer major protocol version will refuse to
  start (`E4A_STORE_VERSION`) instead of corrupting data. Downgrades across
  major versions are not supported; restore from backup.

## Development mode vs. deployment

Development conveniences that must not be mistaken for deployment defaults:
`E4A_DB_PATH=:memory:`, running with no `E4A_API_TOKEN`, and the legacy
pre-1.0 routes (`/mandates/*`, `/governance/*`, `/gates/*`) which remain
only for prototype tooling and are deprecated in favor of `/v1`.
