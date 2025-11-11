from fastapi import FastAPI
from pydantic import BaseModel
from sdk.python.e4a_sdk.mandate_engine import MandateEngine, MANDATE_SCHEMA
from sdk.python.e4a_sdk.scribe_agent import ScribeAgent
from sdk.python.e4a_sdk.governance_kernel import GovernanceKernel
from sdk.python.e4a_sdk.reputation_index import ReputationIndex
from sdk.python.e4a_sdk.gate_engine import GateEngine, GateEngineError

def create_app():
    app = FastAPI(title="E4A Protocol API", version="1.0")

    scribe = ScribeAgent(node_id="api-node")
    engine = MandateEngine(scribe)
    gov = GovernanceKernel()
    rep = ReputationIndex()

    class IntentPart(BaseModel):
        goal: str
        expected_outcome: str
        contextual_tone: str
        statistical_purpose: str
        requires_approval: list[str] = []

    class MandateRequest(BaseModel):
        issuer: str
        beneficiary: str
        amount: float
        currency: str = "USD"
        intent: IntentPart



    @app.post("/mandates/create")
    def create_mandate(req: MandateRequest):
        print(f"DEBUG: Mandate received by API: {req.model_dump()}") # DEBUG PRINT
        result = engine.create_mandate(req.model_dump())
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


    @app.get("/gates/pending")
    def get_pending_gates():
        pending_gates = [gate for gate in engine.gate_engine.gates.values() if gate['status'] == 'pending']
        return {"pending_gates": pending_gates}


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


    @app.get("/health")
    def health_check():
        return {"status": "ok", "entries": len(scribe.ledger)}

    return app
