"""
E4A SDK for Python — reference implementation of E4A protocol 1.0.
"""

__all__ = [
    'Config',
    'GateEngine',
    'GateEngineError',
    'GovernanceKernel',
    'MandateEngine',
    'MandateEngineError',
    'ReputationIndex',
    'ScribeAgent',
    'ValidatorRuntime',
    'E4AClient',
    'E4AError',
    'E4AProtocolError',
    'InMemoryStore',
    'SQLiteStore',
    'PROTOCOL_VERSION',
]

from .config_loader import Config
from .errors import E4AError as E4AProtocolError
from .gate_engine import GateEngine, GateEngineError
from .governance_kernel import GovernanceKernel
from .mandate_engine import MandateEngine, MandateEngineError
from .reputation_index import ReputationIndex
from .schema import PROTOCOL_VERSION
from .scribe_agent import ScribeAgent
from .store import InMemoryStore, SQLiteStore
from .validator_runtime import ValidatorRuntime
from .client import E4AClient, E4AError
