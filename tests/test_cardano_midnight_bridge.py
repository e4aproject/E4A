from core.scribe_agent import ScribeAgent
from core.mandate_engine import MandateEngine
from adapters.universal_rail_adapter.cardano_midnight_bridge import CardanoMidnightBridge
from core.governance_kernel import GovernanceKernel
from core.reputation_index import ReputationIndex


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
        'currency': 'USD'
    })

    # bridge and settle
    bridge = CardanoMidnightBridge()
    res = bridge.bridge_and_settle(m)
    assert 'anchor_ref' in res and 'settlement_tx' in res

    # governance: register charter and submit+enact a proposal
    g = GovernanceKernel()
    ch = g.register_charter('charter-x', {'name': 'Test Charter'})
    assert ch['charter_id'] == 'charter-x'

    # prop = g.submit_proposal('charter-x', 'prop-1', {'action': 'test-action'})
    g.vote('prop-1', 'validator-1', 'yes')
    out = g.simulate_and_enact('prop-1', quorum=1)
    assert out['status'] == 'enacted'

    # reputation: ingest event and check score
    r = ReputationIndex()
    r.ingest_event('did:example:validator-1', 'positive_behavior', weight=3.0)
    score = r.get_score('did:example:validator-1')
    assert 0.0 < score <= 1.0
