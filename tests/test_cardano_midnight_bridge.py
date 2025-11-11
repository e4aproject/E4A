from sdk.python.e4a_sdk.scribe_agent import ScribeAgent
from sdk.python.e4a_sdk.mandate_engine import MandateEngine
from adapters.universal_rail_adapter.cardano_midnight_bridge import CardanoMidnightBridge
from sdk.python.e4a_sdk.governance_kernel import GovernanceKernel
from sdk.python.e4a_sdk.reputation_index import ReputationIndex


def test_bridge_and_governance(tmp_path):
    # prepare scribe + mandate engine
    log = tmp_path / 'mission_log.jsonl'
    s = ScribeAgent(log_path=str(log))
    me = MandateEngine(scribe=s)

    # create mandate
    m = me.create_mandate({
        'issuer': 'did:ex:alice',
        'beneficiary': 'did:ex:bob',
        'amount': 7,
        'currency': 'USD',
        'intent': {
            'goal': 'bridge and settle funds',
            'expected_outcome': 'funds settled on Cardano',
            'contextual_tone': 'formal',
            'statistical_purpose': 'facilitate cross-chain transaction'
        }
    })

    # bridge and settle
    bridge = CardanoMidnightBridge()
    res = bridge.bridge_and_settle(m)
    assert 'anchor_ref' in res and 'settlement_tx' in res

    # reputation: ingest event and check score
    r = ReputationIndex()
    r.ingest_event('validator-1', 'positive_behavior', weight=3.0)
    r.ingest_event('validator-2', 'negative_behavior', weight=1.0) # Lower reputation

    # governance: register charter and submit+enact a proposal
    g = GovernanceKernel(reputation_index=r) # Inject the reputation index
    ch = g.register_charter('charter-x', {'name': 'Test Charter'})
    assert ch['charter_id'] == 'charter-x'

    prop = g.submit_proposal('charter-x', 'prop-1', {'action': 'test-action'})
    g.vote('prop-1', 'validator-1', 'yes') # High reputation vote
    g.vote('prop-1', 'validator-2', 'no')  # Low reputation vote
    out = g.simulate_and_enact('prop-1', quorum=2) # Quorum of 2 to ensure both votes are considered
    assert out['status'] == 'enacted'
    assert out['weighted_votes']['yes'] > out['weighted_votes']['no']

    score = r.get_score('validator-1')
    assert 0.0 < score <= 1.0
