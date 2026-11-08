# API Reference

## Protocol 1.0 API (spec §11) — current

All errors use the envelope `{"error": {"code": "<E4A_*>", "message": "..."}}`.
Branch on `code`, never on `message`. If the service is started with
`E4A_API_TOKEN` set, `/v1` requests require `Authorization: Bearer <token>`.

| Endpoint | Description |
|---|---|
| `POST /v1/mandates` | Submit a mandate (canonical schema). `201` with the mandate record, including `status` and, when approval is required, its `gate_id`. Replaying an identical `(issuer, replay_nonce)` returns the original record; conflicting reuse fails `409 E4A_NONCE_CONFLICT`. Invalid mandates fail `400 E4A_VALIDATION_FAILED`. |
| `GET /v1/mandates/{id}` | Fetch a mandate record (`404 E4A_NOT_FOUND`). |
| `POST /v1/mandates/{id}/decisions` | Record an approval decision. Body: `{"actor": "<id>", "decision": "approve" \| "reject"}`. The `X-E4A-Actor` header, if sent, must agree with `actor`. Unauthorized actors fail `403 E4A_UNAUTHORIZED_APPROVER`. |
| `POST /v1/mandates/{id}/execute` | Execute an approved (or ungated) mandate. Blocked states fail `409` with `E4A_APPROVAL_REQUIRED`, `E4A_MANDATE_REJECTED`, `E4A_MANDATE_EXPIRED`, or `E4A_INVALID_TRANSITION`. The result carries `"mock": true` — execution is simulated in the reference implementation. |
| `GET /v1/mandates/{id}/audit` | Audit records for the mandate (spec §10 shape). |

Service endpoints (no token required):

| Endpoint | Description |
|---|---|
| `GET /health` | Liveness. |
| `GET /ready` | Readiness: store reachable, protocol version, persistence and auth flags. |

See `docs/deployment.md` for configuration, persistence, and the security
posture of the reference service.

## Legacy prototype routes — deprecated

Kept working for existing prototype tooling and tests; **do not build on
these**. They predate the 1.0 lifecycle and error model.

- `POST /mandates/create`, `POST /mandates/execute/{id}`
- `GET /reputation`
- `POST /governance/propose`, `POST /governance/vote`, `POST /governance/enact`
- `GET /gates/pending`, `POST /gates/{id}/approve`, `POST /gates/{id}/reject`
