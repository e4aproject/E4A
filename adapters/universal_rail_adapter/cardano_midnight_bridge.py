"""
Cardano <-> Midnight Bridge (simulated)

Uses MidnightAdapter and EthAdapter to create confidential contracts and anchor them to L1.
Provides a convenience function `bridge_and_settle` that performs the flow end-to-end.
"""
from datetime import datetime, timezone
from adapters.universal_rail_adapter.midnight_adapter import MidnightAdapter
from adapters.universal_rail_adapter.eth_adapter import EthAdapter

class BridgeError(Exception):
    pass

class CardanoMidnightBridge:
    def __init__(self, midnight=None, settlement_adapter=None):
        self.midnight = midnight or MidnightAdapter()
        self.settlement = settlement_adapter or EthAdapter(chain_name='ethereum')

    def bridge_and_settle(self, mandate_payload):
        # 1) create confidential contract on Midnight
        created = self.midnight.create_confidential_contract(mandate_payload)
        if not created or 'anchor_ref' not in created:
            raise BridgeError('midnight_creation_failed')
        anchor_ref = created['anchor_ref']

        # 2) submit anchor to settlement (simulate Cardano/Ethereum L1)
        tx = self.settlement.submit_anchor(anchor_ref)
        if tx.get('status') != 'submitted':
            raise BridgeError('settlement_submission_failed')
        tx_hash = tx.get('tx_hash')

        # 3) publish settlement_ref back to Midnight store
        pub = self.midnight.publish_anchor(anchor_ref, settlement_ref=tx_hash)
        if pub.get('status') != 'published':
            raise BridgeError('publish_failed')

        return {
            'anchor_ref': anchor_ref,
            'settlement_tx': tx_hash,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
