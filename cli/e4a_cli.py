# cli/e4a_cli.py
import typer
import json
from core.mandate_engine import MandateEngine
from core.scribe_agent import ScribeAgent
from core.reputation_index import ReputationIndex
from core.governance_kernel import GovernanceKernel
from core.config_loader import load_config
from e4a_sdk.client import E4AClient

cfg = load_config()
client = E4AClient(base_url=cfg.get("api")["host"], timeout=cfg.get("api")["timeout"])
# then in commands, optionally call client.create_mandate etc. if you prefer remote mode

app = typer.Typer(help="E4A Protocol CLI")

scribe = ScribeAgent(node_id="cli-node")
engine = MandateEngine(scribe)
gov = GovernanceKernel()
rep = ReputationIndex()

@app.command()
def mandate_create(issuer: str, beneficiary: str, amount: float, currency: str = "USD"):
    """Create a new mandate"""
    result = engine.create_mandate({
        "issuer": issuer,
        "beneficiary": beneficiary,
        "amount": amount,
        "currency": currency
    })
    typer.echo(json.dumps(result, indent=2))

@app.command()
def mandate_execute(mandate_id: str):
    """Execute a mandate"""
    result = engine.execute_mandate(mandate_id)
    typer.echo(json.dumps(result, indent=2))

@app.command()
def governance_propose(pid: str, action: str, description: str):
    """Propose a governance action"""
    out = gov.propose(pid, action, description)
    typer.echo(json.dumps(out, indent=2))

@app.command()
def governance_vote(pid: str, vote: str):
    """Vote on a proposal"""
    out = gov.vote(pid, vote)
    typer.echo(json.dumps(out, indent=2))

@app.command()
def governance_enact(pid: str):
    """Enact a proposal"""
    out = gov.enact(pid)
    typer.echo(json.dumps(out, indent=2))

@app.command()
def reputation_view():
    """Display current reputation index"""
    rep.ingest_from_scribe(scribe)
    typer.echo(json.dumps(rep.get_all(), indent=2))

@app.command()
def ledger_show():
    """Show full scribe ledger"""
    typer.echo(json.dumps(scribe.ledger, indent=2))

if __name__ == "__main__":
    app()
