# Quickstart: The E4A Developer Flow
This document demonstrates the minimal end-to-end flow, from mandate creation to validation and anchoring.
### 1. Create a Mandate via Adapter
\`\`\`python
# Run from repository root
from adapters.a2a.adapter import E4A_A2A_Adapter
adapter = E4A_A2A_Adapter()
mandate = {"issuer":"did:ex:alice", "beneficiary":"did:ex:bob","amount":1,"currency":"USD", "mandate_id":"test-01"}
created = adapter.create_mandate(mandate)
print(created)
\`\`\`
### 2. Validate the Schema
`python -m tools.validator specs/mandate_v1.json examples/sample_mandate.json`
### 3. Canonicalize & Hash
`python -m tools.mission_log_canonicalizer examples/sample_mandate.json`
### 4. Anchor the Hash
Start mock server: `python -m adapters.universal_rail_adapter.mock_server`
Post the hash: `curl -X POST http://localhost:8080/anchor -H "Content-Type: application/json" -d '{"content_hash":"YOUR_HASH"}'`
