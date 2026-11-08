"""Mandate lifecycle commands for the E4A CLI.

These commands drive the reference SDK in-process, backed by a local
SQLite store so mandates persist across invocations. The store path is
``$E4A_DB_PATH`` when set, otherwise ``~/.e4a/e4a.db`` (the same default
file name the reference service uses when run from a home directory).

Identities are asserted strings (protocol 1.0 has no cryptographic
identity; see docs/protocol/spec.md section 9), and execution is a mock:
no external effect occurs.
"""

import json
import os
import uuid
from pathlib import Path

import typer

from e4a_sdk import errors
from e4a_sdk.mandate_engine import MandateEngine, MandateEngineError
from e4a_sdk.scribe_agent import ScribeAgent
from e4a_sdk.store import SQLiteStore

app = typer.Typer(help="Work with E4A mandates (create, decide, execute, audit).")


def _db_path() -> Path:
    configured = os.environ.get("E4A_DB_PATH")
    if configured:
        return Path(configured)
    return Path.home() / ".e4a" / "e4a.db"


def _engine() -> MandateEngine:
    db_path = _db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    store = SQLiteStore(str(db_path))
    scribe = ScribeAgent(node_id="e4a-cli", log_path=str(db_path.parent / "mission_log.jsonl"))
    return MandateEngine(store=store, scribe=scribe)


def _emit(result) -> None:
    typer.echo(json.dumps(result, indent=2))


def _fail(exc: MandateEngineError) -> None:
    payload = {"error": {"code": exc.code, "message": str(exc)}}
    typer.echo(json.dumps(payload, indent=2))
    raise typer.Exit(code=1)


@app.command("create")
def mandate_create(
    issuer: str = typer.Option(..., "--issuer", help="Asserted issuer identifier."),
    beneficiary: str = typer.Option(..., "--beneficiary", help="Asserted beneficiary identifier."),
    goal: str = typer.Option(..., "--goal", help="Intent: what this mandate is for."),
    expected_outcome: str = typer.Option("mandate executed", "--expected-outcome"),
    contextual_tone: str = typer.Option("neutral", "--tone"),
    statistical_purpose: str = typer.Option("operational record", "--purpose"),
    amount: float = typer.Option(None, "--amount", help="Optional amount (requires --currency)."),
    currency: str = typer.Option(None, "--currency"),
    requires_approval: list[str] = typer.Option(  # noqa: B008 - typer pattern
        None, "--requires-approval", help="Approver identifier; repeat for multiple approvers."
    ),
    nonce: str = typer.Option(None, "--nonce", help="Replay nonce; generated when omitted."),
    expires_at: str = typer.Option(None, "--expires-at", help="ISO-8601 expiry timestamp."),
):
    """Create a mandate and print it as JSON."""
    mandate: dict = {
        "issuer": issuer,
        "beneficiary": beneficiary,
        "replay_nonce": nonce or f"cli-{uuid.uuid4().hex}",
        "intent": {
            "goal": goal,
            "expected_outcome": expected_outcome,
            "contextual_tone": contextual_tone,
            "statistical_purpose": statistical_purpose,
        },
    }
    if amount is not None:
        mandate["amount"] = amount
        mandate["currency"] = currency or "USD"
    if requires_approval:
        mandate["intent"]["requires_approval"] = list(requires_approval)
    if expires_at:
        mandate["expires_at"] = expires_at
    try:
        _emit(_engine().create_mandate(mandate))
    except MandateEngineError as exc:
        _fail(exc)


@app.command("get")
def mandate_get(mandate_id: str):
    """Print one mandate as JSON."""
    try:
        _emit(_engine().get_mandate(mandate_id))
    except MandateEngineError as exc:
        _fail(exc)


@app.command("decide")
def mandate_decide(
    mandate_id: str,
    actor: str = typer.Option(..., "--actor", help="Asserted approver identifier."),
    decision: str = typer.Option(..., "--decision", help="'approve' or 'reject'."),
):
    """Record an approval decision for a gated mandate."""
    if decision not in ("approve", "reject"):
        typer.echo(
            json.dumps(
                {"error": {"code": errors.VALIDATION_FAILED, "message": "decision must be 'approve' or 'reject'"}}
            )
        )
        raise typer.Exit(code=1)
    try:
        _emit(_engine().record_decision(mandate_id, actor, decision))
    except MandateEngineError as exc:
        _fail(exc)


@app.command("execute")
def mandate_execute(mandate_id: str):
    """Execute an approved (or ungated) mandate. Execution is a mock."""
    try:
        _emit(_engine().execute_mandate(mandate_id))
    except MandateEngineError as exc:
        _fail(exc)


@app.command("audit")
def mandate_audit(mandate_id: str):
    """Print the audit trail for a mandate as JSON."""
    try:
        _emit(_engine().get_audit(mandate_id))
    except MandateEngineError as exc:
        _fail(exc)
