# examples/demo_full_run.py
from core.scribe_agent import ScribeAgent
from core.mandate_engine import MandateEngine
from core.reputation_index import ReputationIndex
from core.governance_kernel import GovernanceKernel
import json

scribe = ScribeAgent(node_id="demo-node")
engine = MandateEngine(scribe)
rep = ReputationIndex()
gov = GovernanceKernel()

print("=== DEMO: E4A Full System Run ===")

m = engine.create_mandate({"issuer": "did:ex:alice", "beneficiary": "did:ex:bob", "amount": 42})
print("Mandate created:", json.dumps(m, indent=2))

result = engine.execute_mandate(m["mandate_id"])
print("Mandate executed:", json.dumps(result, indent=2))

rep.ingest_from_scribe(scribe)
print("Reputation index:", json.dumps(rep.get_all(), indent=2))

gov.propose("p1", "upgrade_protocol", "Enable hybrid validation and reputation bonding.")
gov.vote("p1", "yes")
gov.enact("p1")

print("Governance enacted:", json.dumps(gov.proposals["p1"], indent=2))

print("\nLedger snapshot:")
print(json.dumps(scribe.ledger, indent=2))
