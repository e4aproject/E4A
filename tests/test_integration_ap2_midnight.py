import os
from core.scribe_agent import ScribeAgent
from core.mandate_engine import MandateEngine
from adapters.ap2.ap2_client import AP2Client
from adapters.universal_rail_adapter.midnight_adapter import MidnightAdapter
from adapters.universal_rail_adapter.eth_adapter import EthAdapter

def test_ap2_create_sign_submit_and_midnight_anchor(tmp_path):
    # Setup
    log = tmp_path / "mission_log.jsonl"
    s = ScribeAgent(log_path=str(log))
    me = MandateEngine(scribe=s)

    # Create mandate
    mandate = me.create_mandate({
        "issuer": "did:ex:alice",
        "beneficiary": "did:ex:bob",
        "amount": 42,
        "currency": "USD",
        "fee_distribution": {"protocol": 0.01, "validator": 0.01, "issuer": 0}
    })

    # AP2 flow
    ap2 = AP2Client()
    create_r = ap2.create(mandate)
    assert create_r.get("status") == "created"
    # sign
    sign_r = ap2.sign(mandate['mandate_id'], signer="tester")
    assert sign_r.get("status") == "signed"
    # submit
    submit_r = ap2.submit(mandate['mandate_id'])
    assert submit_r.get("status") == "settled"

    # Midnight confidential contract
    mid = MidnightAdapter()
    conf = mid.create_confidential_contract(mandate)
    assert 'anchor_ref' in conf
    anchor_ref = conf['anchor_ref']

    # Simulate anchor publish to an L1 (eth adapter)
    eth = EthAdapter(chain_name='ethereum-test')
    tx = eth.submit_anchor(anchor_ref)
    assert tx.get('status') == 'submitted'
    tx_hash = tx.get('tx_hash')
    # publish settlement link
    pub = mid.publish_anchor(anchor_ref, settlement_ref=tx_hash)
    assert pub.get('status') == 'published'
