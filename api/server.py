"""
E4A reference service — protocol 1.0 API profile (spec section 11) plus the
legacy prototype routes (deprecated, kept working for existing tests/tools).

Configuration (environment variables, validated at startup):
- E4A_DB_PATH: SQLite database file for persistent storage.
  Default: ./data/e4a-v1.db (created if missing). Set to ":memory:" for an
  ephemeral in-memory store (development/tests only — data does not survive
  a restart, and the service logs a warning saying so).
- E4A_API_TOKEN: if set, every /v1 request must carry
  "Authorization: Bearer <token>". If unset, /v1 is open (development mode).
  This is a shared-secret gate for the reference deployment, NOT protocol
  authentication: per spec section 9, E4A 1.0 actor identities are asserted
  (for decisions, via the X-E4A-Actor header or the body's "actor" field),
  never cryptographically verified. Do not expose this service publicly
  without a real authentication layer in front of it.

Errors on /v1 routes use the spec envelope:
    {"error": {"code": "<E4A_* stable code>", "message": "<detail>"}}
Clients must branch on code, never on message text.
"""

import logging
import os

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from e4a_sdk import errors
from e4a_sdk.errors import E4AError
from e4a_sdk.gate_engine import GateEngineError
from e4a_sdk.governance_kernel import GovernanceKernel
from e4a_sdk.mandate_engine import MandateEngine, MandateEngineError
from e4a_sdk.reputation_index import ReputationIndex
from e4a_sdk.schema import PROTOCOL_VERSION
from e4a_sdk.scribe_agent import ScribeAgent
from e4a_sdk.store import InMemoryStore, SQLiteStore

logger = logging.getLogger("e4a.api")

# Spec section 11: stable code -> HTTP status
HTTP_FOR_CODE = {
    errors.VALIDATION_FAILED: 400,
    errors.UNSUPPORTED_VERSION: 400,
    errors.NOT_FOUND: 404,
    errors.UNAUTHORIZED_APPROVER: 403,
    errors.APPROVAL_REQUIRED: 409,
    errors.MANDATE_REJECTED: 409,
    errors.MANDATE_EXPIRED: 409,
    errors.INVALID_TRANSITION: 409,
    errors.NONCE_CONFLICT: 409,
    errors.EXECUTION_FAILED: 500,
    errors.STORE_VERSION: 500,
}


def _error_response(exc):
    code = getattr(exc, "code", errors.EXECUTION_FAILED)
    status = HTTP_FOR_CODE.get(code, 500)
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "message": str(exc)}},
    )


def _make_store(db_path):
    if db_path == ":memory:":
        logger.warning(
            "E4A_DB_PATH=:memory: — data will NOT survive a restart (development mode)"
        )
        return InMemoryStore(), False
    directory = os.path.dirname(os.path.abspath(db_path))
    os.makedirs(directory, exist_ok=True)
    return SQLiteStore(db_path), True


def create_app(db_path=None, api_token=None):
    db_path = db_path if db_path is not None else os.environ.get("E4A_DB_PATH", "./data/e4a-v1.db")
    api_token = api_token if api_token is not None else os.environ.get("E4A_API_TOKEN")
    if api_token == "":
        api_token = None  # empty means unset (e.g. a blank compose variable)

    store, persistent = _make_store(db_path)
    scribe = ScribeAgent(node_id="api-node")
    engine = MandateEngine(scribe=scribe, store=store)
    gov = GovernanceKernel()
    rep = ReputationIndex()

    app = FastAPI(title="E4A Protocol API", version=PROTOCOL_VERSION)
    app.state.engine = engine
    app.state.store = store
    app.state.persistent = persistent

    @app.exception_handler(E4AError)
    async def _e4a_error_handler(request: Request, exc: E4AError):
        logger.info("protocol error on %s: %s (%s)", request.url.path, exc.code, exc)
        return _error_response(exc)

    def require_token(authorization: str = Header(default=None)):
        if api_token is not None:
            if authorization != f"Bearer {api_token}":
                raise HTTPException(
                    status_code=401,
                    detail={"error": {"code": "E4A_UNAUTHORIZED", "message": "Missing or invalid API token"}},
                )

    v1 = [Depends(require_token)]

    # ------------------------------------------------------------------
    # Service health
    # ------------------------------------------------------------------
    @app.get("/health")
    def health_check():
        """Liveness: the process is up."""
        return {"status": "ok", "entries": len(scribe.ledger)}

    @app.get("/ready")
    def readiness_check():
        """Readiness: the store answers and speaks our protocol version."""
        try:
            store.all_mandates()
        except Exception as exc:  # pragma: no cover - defensive
            return JSONResponse(
                status_code=503,
                content={"status": "not_ready", "error": {"code": "E4A_STORE_UNAVAILABLE", "message": str(exc)}},
            )
        return {
            "status": "ready",
            "protocol_version": PROTOCOL_VERSION,
            "persistent": persistent,
            "auth_required": api_token is not None,
        }

    # ------------------------------------------------------------------
    # Protocol 1.0 API (spec section 11)
    # ------------------------------------------------------------------
    @app.post("/v1/mandates", status_code=201, dependencies=v1)
    def v1_create_mandate(payload: dict):
        # Idempotent replays return the original record (spec section 6).
        return engine.create_mandate(payload)

    @app.get("/v1/mandates/{mandate_id}", dependencies=v1)
    def v1_get_mandate(mandate_id: str):
        return engine.get_mandate(mandate_id)

    class DecisionRequest(BaseModel):
        actor: str
        decision: str  # "approve" | "reject"

    @app.post("/v1/mandates/{mandate_id}/decisions", dependencies=v1)
    def v1_record_decision(
        mandate_id: str,
        req: DecisionRequest,
        x_e4a_actor: str = Header(default=None),
    ):
        # The decision actor is the body's "actor"; the X-E4A-Actor header,
        # when present, must agree with it (asserted identity, spec section 9).
        if x_e4a_actor is not None and x_e4a_actor != req.actor:
            raise HTTPException(
                status_code=400,
                detail={"error": {"code": errors.VALIDATION_FAILED,
                                  "message": "X-E4A-Actor header disagrees with body actor"}},
            )
        return engine.record_decision(mandate_id, req.actor, req.decision)

    @app.post("/v1/mandates/{mandate_id}/execute", dependencies=v1)
    def v1_execute_mandate(mandate_id: str, x_e4a_actor: str = Header(default=None)):
        result = engine.execute_mandate(mandate_id, executor_id=x_e4a_actor or "api")
        record = engine.get_mandate(mandate_id)
        return {"mandate_id": mandate_id, "status": record["status"], "result": result}

    @app.get("/v1/mandates/{mandate_id}/audit", dependencies=v1)
    def v1_get_audit(mandate_id: str):
        return {"mandate_id": mandate_id, "audit": engine.get_audit(mandate_id)}

    # ------------------------------------------------------------------
    # Legacy prototype routes (deprecated; superseded by /v1 above)
    # ------------------------------------------------------------------
    class IntentPart(BaseModel):
        goal: str
        expected_outcome: str
        contextual_tone: str
        statistical_purpose: str
        requires_approval: list = []

    class MandateRequest(BaseModel):
        issuer: str
        beneficiary: str
        amount: float
        currency: str = "USD"
        intent: IntentPart

    @app.post("/mandates/create")
    def create_mandate_legacy(req: MandateRequest):
        result = engine.create_mandate(req.model_dump())
        return {"status": "created", "mandate": result}

    @app.post("/mandates/execute/{mandate_id}")
    def execute_mandate_legacy(mandate_id: str):
        result = engine.execute_mandate(mandate_id)
        return {"status": "executed", "mandate_id": mandate_id, "result": result}

    @app.get("/reputation")
    def get_reputation():
        rep.ingest_from_scribe(scribe)
        return {"reputation": rep.get_all()}

    class Proposal(BaseModel):
        id: str
        action: str
        description: str

    @app.post("/governance/propose")
    def propose_change(p: Proposal):
        return {"status": "proposed", "proposal": gov.propose(p.id, p.action, p.description)}

    @app.post("/governance/vote")
    def vote_proposal(pid: str, vote: str):
        return {"status": "voted", "result": gov.vote(pid, vote)}

    @app.post("/governance/enact")
    def enact_proposal(pid: str):
        return {"status": "enacted", "result": gov.enact(pid)}

    @app.get("/gates/pending")
    def get_pending_gates():
        pending = [g for g in engine.gate_engine.gates.values() if g["status"] == "pending"]
        return {"pending_gates": pending}

    @app.post("/gates/{gate_id}/approve")
    def approve_gate(gate_id: str, approver_id: str):
        try:
            gate = engine.gate_engine.approve_gate(gate_id, approver_id)
            return {"status": "success", "gate": gate}
        except GateEngineError as e:
            return {"status": "error", "message": str(e)}

    @app.post("/gates/{gate_id}/reject")
    def reject_gate(gate_id: str, rejector_id: str):
        try:
            gate = engine.gate_engine.reject_gate(gate_id, rejector_id)
            return {"status": "success", "gate": gate}
        except GateEngineError as e:
            return {"status": "error", "message": str(e)}

    return app
