import pytest
from sdk.python.e4a_sdk.gate_engine import GateEngine, GateEngineError
from sdk.python.e4a_sdk.mandate_engine import MandateEngine, MandateEngineError
from sdk.python.e4a_sdk.scribe_agent import ScribeAgent


@pytest.fixture
def gate_engine():
    return GateEngine()


@pytest.fixture
def mandate_engine():
    return MandateEngine(scribe=ScribeAgent())


def test_create_gate(gate_engine):
    mandate_id = "test-mandate-1"
    required_approvers = ["human-alice", "human-bob"]
    payload = {"action": "test_action"}
    gate = gate_engine.create_gate(mandate_id, required_approvers, payload)

    assert gate['gate_id'] is not None
    assert gate['mandate_id'] == mandate_id
    assert gate['status'] == 'pending'
    assert gate['required_approvers'] == required_approvers
    assert gate['approvals'] == []
    assert gate['rejections'] == []
    assert 'created_at' in gate
    assert gate['payload'] == payload


def test_get_gate_status(gate_engine):
    mandate_id = "test-mandate-2"
    required_approvers = ["human-charlie"]
    payload = {"action": "another_action"}
    created_gate = gate_engine.create_gate(mandate_id, required_approvers, payload)

    retrieved_gate = gate_engine.get_gate_status(created_gate['gate_id'])
    assert retrieved_gate == created_gate

    with pytest.raises(GateEngineError, match="Gate not found"):
        gate_engine.get_gate_status("non-existent-gate")


def test_approve_gate(gate_engine):
    mandate_id = "test-mandate-3"
    required_approvers = ["human-alice", "human-bob"]
    payload = {"action": "critical_action"}
    gate = gate_engine.create_gate(mandate_id, required_approvers, payload)

    # Alice approves
    gate_engine.approve_gate(gate['gate_id'], "human-alice")
    updated_gate = gate_engine.get_gate_status(gate['gate_id'])
    assert "human-alice" in updated_gate['approvals']
    assert updated_gate['status'] == 'pending'  # Still pending, Bob hasn't approved

    # Bob approves
    gate_engine.approve_gate(gate['gate_id'], "human-bob")
    final_gate = gate_engine.get_gate_status(gate['gate_id'])
    assert "human-bob" in final_gate['approvals']
    assert final_gate['status'] == 'approved'

    # Cannot approve an already approved gate
    with pytest.raises(GateEngineError, match="Gate .* is already approved"):
        gate_engine.approve_gate(gate['gate_id'], "human-alice")


def test_reject_gate(gate_engine):
    mandate_id = "test-mandate-4"
    required_approvers = ["human-diana", "human-eve"]
    payload = {"action": "risky_action"}
    gate = gate_engine.create_gate(mandate_id, required_approvers, payload)

    # Diana rejects
    gate_engine.reject_gate(gate['gate_id'], "human-diana")
    updated_gate = gate_engine.get_gate_status(gate['gate_id'])
    assert "human-diana" in updated_gate['rejections']
    assert updated_gate['status'] == 'rejected'  # One rejection from required approver is enough

    # Cannot reject an already rejected gate
    with pytest.raises(GateEngineError, match="Gate .* is already rejected"):
        gate_engine.reject_gate(gate['gate_id'], "human-diana")


def test_mandate_engine_integration_pending(mandate_engine):
    sample_mandate = {
        'issuer': 'did:ex:agent-x',
        'beneficiary': 'did:ex:agent-y',
        'amount': 500.0,
        'currency': 'USD',
        'intent': {
            'goal': 'perform high-value operation',
            'expected_outcome': 'operation completed',
            'contextual_tone': 'formal',
            'statistical_purpose': 'secure execution',
            'requires_approval': ['human-ceo', 'human-cfo']
        }
    }
    mandate = mandate_engine.create_mandate(sample_mandate)

    with pytest.raises(MandateEngineError, match=r"Mandate .*? requires human approval\. A new gate \(ID: ([a-f0-9-]+)\) has been created and is pending\.") as excinfo:
        mandate_engine.execute_mandate(mandate['mandate_id'])

    import re
    match = re.search(r'\(ID: ([a-f0-9-]+)\)', str(excinfo.value))
    if match:
        gate_id = match.group(1)
    else:
        raise ValueError("Regex did not find Gate ID in error message.")

    # Verify a gate was created
    gate = mandate_engine.gate_engine.get_gate_status(gate_id)
    assert gate['status'] == 'pending'
    assert gate['mandate_id'] == mandate['mandate_id']


def test_mandate_engine_integration_approved(mandate_engine):
    sample_mandate = {
        'issuer': 'did:ex:agent-a',
        'beneficiary': 'did:ex:agent-b',
        'amount': 200.0,
        'currency': 'USD',
        'intent': {
            'goal': 'perform routine task',
            'expected_outcome': 'task completed',
            'contextual_tone': 'informal',
            'statistical_purpose': 'efficient processing',
            'requires_approval': ['human-manager']
        }
    }
    mandate = mandate_engine.create_mandate(sample_mandate)

    # Attempt execution, expect pending error and gate creation
    with pytest.raises(MandateEngineError, match=r"Mandate .*? requires human approval\. A new gate \(ID: ([a-f0-9-]+)\) has been created and is pending\.") as excinfo:
        mandate_engine.execute_mandate(mandate['mandate_id'])

    import re
    match = re.search(r'\(ID: ([a-f0-9-]+)\)', str(excinfo.value))
    if match:
        gate_id = match.group(1)
    else:
        raise ValueError("Regex did not find Gate ID in error message.")

    # Approve the gate
    mandate_engine.gate_engine.approve_gate(gate_id, 'human-manager')
    approved_gate = mandate_engine.gate_engine.get_gate_status(gate_id)
    assert approved_gate['status'] == 'approved'

    # Now execute the mandate, should succeed
    result = mandate_engine.execute_mandate(mandate['mandate_id'])
    assert result['status'] == 'executed'


def test_mandate_engine_integration_rejected(mandate_engine):
    sample_mandate = {
        'issuer': 'did:ex:agent-c',
        'beneficiary': 'did:ex:agent-d',
        'amount': 700.0,
        'currency': 'USD',
        'intent': {
            'goal': 'critical data deletion',
            'expected_outcome': 'data removed',
            'contextual_tone': 'urgent',
            'statistical_purpose': 'data hygiene',
            'requires_approval': ['human-data-owner']
        }
    }
    mandate = mandate_engine.create_mandate(sample_mandate)

    # Attempt execution, expect pending error and gate creation
    with pytest.raises(MandateEngineError, match=r"Mandate .*? requires human approval\. A new gate \(ID: ([a-f0-9-]+)\) has been created and is pending\.") as excinfo:
        mandate_engine.execute_mandate(mandate['mandate_id'])

    import re
    match = re.search(r'\(ID: ([a-f0-9-]+)\)', str(excinfo.value))
    if match:
        gate_id = match.group(1)
    else:
        raise ValueError("Regex did not find Gate ID in error message.")

    # Reject the gate
    mandate_engine.gate_engine.reject_gate(gate_id, 'human-data-owner')
    rejected_gate = mandate_engine.gate_engine.get_gate_status(gate_id)
    assert rejected_gate['status'] == 'rejected'

    # Attempt execution again, should fail with rejected error
    with pytest.raises(MandateEngineError, match="was rejected by human approvers"):
        mandate_engine.execute_mandate(mandate['mandate_id'])
