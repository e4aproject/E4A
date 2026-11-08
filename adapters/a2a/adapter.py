# adapters/a2a/adapter.py
from typing import Dict, Any

from e4a_sdk.mandate_engine import MandateEngine, MandateEngineError
from e4a_sdk.governance_kernel import GovernanceKernel
from e4a_sdk.scribe_agent import ScribeAgent

# NOTE (E4A 1.0): this adapter performs no schema validation of its own.
# There is exactly one validation path — the MandateEngine validates against
# the canonical protocol schema bundled in the SDK (spec section 13.1).
# The previous behavior (adapter validating against specs/mandate_v1.json
# while the engine required the v2/intent shape) made the adapter flow fail
# end to end.

class E4A_A2A_Adapter:
    """
    The E4A_A2A_Adapter provides a bridge between the E4A SDK and an A2A (Agent-to-Agent) network.
    It exposes the core functionality of the MandateEngine and GovernanceKernel to other agents.
    """
    def __init__(self, scribe: ScribeAgent = None):
        """
        Initializes the E4A_A2A_Adapter.

        Args:
            scribe: An optional ScribeAgent instance. If not provided, a new one will be created.
        """
        self.scribe = scribe or ScribeAgent()
        self.mandate_engine = MandateEngine(scribe=self.scribe)
        self.gov = GovernanceKernel()

    def create_mandate(self, data_part: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a new mandate.

        This method validates the input data against the mandate schema, creates the mandate
        using the MandateEngine, records the creation in the scribe, and returns the result.

        Args:
            data_part: A dictionary containing the mandate data.

        Returns:
            A dictionary containing the status and the created mandate.
        """
        mandate = self.mandate_engine.create_mandate(data_part)
        self.scribe.record("mandate_created", payload=mandate, summary="Mandate created via A2A Adapter")
        return {"status": "created", "mandate": mandate}
