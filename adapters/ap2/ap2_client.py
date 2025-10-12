"""
AP2 Client (reference stub)
Uses the AP2MockServer for local simulation.
Implements create -> sign -> submit and create_submandate behavior.
"""

#import os
#from ..ap2.ap2_mock_server import AP2MockServer

class AP2ClientError(Exception):
    pass

class AP2Client:
    def __init__(self, server=None):
        self.server = server or AP2MockServer()

    def create(self, mandate_payload):
        return self.server.create(mandate_payload)

    def sign(self, mandate_id, signer="ap2-client"):
        return self.server.sign(mandate_id, signer=signer)

    def submit(self, mandate_id):
        return self.server.submit(mandate_id)

    def create_submandate(self, parent_mandate, subpayload, mandate_engine=None):
        """
        Convenience: create a submandate using MandateEngine semantics + AP2 create/sign/submit.
        mandate_engine (optional): if provided, use it to persist and enforce inheritance logic.
        Returns submission result.
        """
        if mandate_engine:
            # let engine handle conditional inheritance
            sub = mandate_engine.create_submandate(parent_mandate['mandate_id'], subpayload)
        else:
            sub = dict(subpayload)
        # Create -> sign -> submit on mock server
        create_r = self.create(sub)
        mid = create_r.get('mandate_id') or sub.get('mandate_id')
        self.sign(mid)
        return self.submit(mid)
