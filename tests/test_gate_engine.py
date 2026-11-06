import pytest
from e4a_sdk.gate_engine import GateEngine, GateEngineError
from e4a_sdk.mandate_engine import MandateEngine, MandateEngineError
from e4a_sdk.scribe_agent import ScribeAgent


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
    # Spec 1.0 behavior (supersedes the prototype's lazy gate creation):
    # the gate is created at submission, the mandate is pending_approval,
    # and execution fails with the stable code E4A_APPROVAL_REQUIRED.
    from e4a_sdk import errors
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
    assert mandate['status'] == 'pending_approval'

    gate = mandate_engine.gate_engine.get_gate_by_mandate_id(mandate['mandate_id'])
    assert gate is not None
    assert gate['status'] == 'pending'
    assert gate['mandate_id'] == mandate['mandate_id']

    with pytest.raises(MandateEngineError) as excinfo:
        mandate_engine.execute_mandate(mandate['mandate_id'])
    assert excinfo.value.code == errors.APPROVAL_REQUIRED


def test_mandate_engine_integration_approved(mandate_engine):
    from e4a_sdk import errors
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

    with pytest.raises(MandateEngineError) as excinfo:
        mandate_engine.execute_mandate(mandate['mandate_id'])
    assert excinfo.value.code == errors.APPROVAL_REQUIRED

    decided = mandate_engine.record_decision(mandate['mandate_id'], 'human-manager', 'approve')
    assert decided['status'] == 'approved'

    result = mandate_engine.execute_mandate(mandate['mandate_id'])
    assert result['status'] == 'executed'
    assert result['mock'] is True


def test_mandate_engine_integration_rejected(mandate_engine):
    from e4a_sdk import errors
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

    decided = mandate_engine.record_decision(mandate['mandate_id'], 'human-data-owner', 'reject')
    assert decided['status'] == 'rejected'

    with pytest.raises(MandateEngineError) as excinfo:
        mandate_engine.execute_mandate(mandate['mandate_id'])
    assert excinfo.value.code == errors.MANDATE_REJECTED
