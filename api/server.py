# api/server.py
from fastapi import FastAPI
from pydantic import BaseModel
from sdk.python.e4a_sdk.mandate_engine import MandateEngine
from sdk.python.e4a_sdk.scribe_agent import ScribeAgent
from sdk.python.e4a_sdk.governance_kernel import GovernanceKernel
from sdk.python.e4a_sdk.reputation_index import ReputationIndex

app = FastAPI(title="E4A Protocol API", version="1.0")

scribe = ScribeAgent(node_id="api-node")
engine = MandateEngine(scribe)
gov = GovernanceKernel()
rep = ReputationIndex()


class MandateRequest(BaseModel):
    issuer: str
    beneficiary: str
    amount: float
    currency: str = "USD"


@app.post("/mandates/create")
def create_mandate(req: MandateRequest):
    result = engine.create_mandate(req.dict())
    return {"status": "created", "mandate": result}


@app.post("/mandates/execute/{mandate_id}")
def execute_mandate(mandate_id: str):
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


@app.get("/health")
def health_check():
    return {"status": "ok", "entries": len(scribe.ledger)}
