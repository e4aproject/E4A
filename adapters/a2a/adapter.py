# adapters/a2a/adapter.py
import json
from pathlib import Path
from typing import Dict, Any
from jsonschema import validate, ValidationError

# Assumes SDK is structured as sdk/python/e4a_sdk
from sdk.python.e4a_sdk.mandate_engine import MandateEngine, MandateEngineError
from sdk.python.e4a_sdk.governance_kernel import GovernanceKernel
from sdk.python.e4a_sdk.scribe_agent import ScribeAgent

SPEC_DIR = Path(__file__).resolve().parents[2] / "specs"

def _load_schema(name: str) -> Dict[str, Any]:
    path = SPEC_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Schema not found: {path}")
    return json.loads(path.read_text())

MANDATE_SCHEMA = _load_schema("mandate_v1.json")

class E4A_A2A_Adapter:
    def __init__(self, scribe: ScribeAgent = None):
        self.scribe = scribe or ScribeAgent()
        self.mandate_engine = MandateEngine(scribe=self.scribe)
        self.gov = GovernanceKernel()

    def _validate(self, payload: Dict[str, Any], schema_name: str):
        schema = _load_schema(schema_name)
        try:
            validate(instance=payload, schema=schema)
        except ValidationError as e:
            raise ValueError(f"Payload failed schema validation: {e.message}")

    def create_mandate(self, data_part: Dict[str, Any]) -> Dict[str, Any]:
        """Skill: create-mandate"""
        self._validate(data_part, "mandate_v1.json")
        mandate = self.mandate_engine.create_mandate(data_part)
        self.scribe.record("mandate_created", payload=mandate, summary="Mandate created via A2A Adapter")
        return {"status": "created", "mandate": mandate}
