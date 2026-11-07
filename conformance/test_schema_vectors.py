"""Spec section 3 conformance: the schema vectors in docs/protocol/test-vectors.

Each vector file carries a mandate document plus `expect` ("valid"/"invalid")
and, for invalid documents, the spec section 14 error code the implementation
MUST surface. Expectations come from the vector files themselves and from
direct validation against the normative schema — never from implementation
internals.
"""

import json

import jsonschema
import pytest

from conftest import SCHEMA_PATH, load_json, schema_vector_files

VECTORS = [(p, load_json(p)) for p in schema_vector_files()]
IDS = [p.name for p, _ in VECTORS]


@pytest.mark.parametrize("path,vector", VECTORS, ids=IDS)
def test_vector_against_normative_schema(path, vector):
    schema = load_json(SCHEMA_PATH)
    mandate = vector["mandate"]
    if vector["expect"] == "valid":
        jsonschema.validate(instance=mandate, schema=schema)
    else:
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=mandate, schema=schema)


@pytest.mark.parametrize("path,vector", VECTORS, ids=IDS)
def test_vector_against_implementation(engine, path, vector):
    from conftest import error_code

    mandate = json.loads(json.dumps(vector["mandate"]))  # deep copy
    mandate.pop("mandate_id", None)  # ids are server-assigned in the API profile
    if vector["expect"] == "valid":
        created = engine.create_mandate(mandate)
        assert created["mandate_id"]
    else:
        with pytest.raises(Exception) as excinfo:
            engine.create_mandate(mandate)
        assert error_code(excinfo.value) == vector.get("error_code", "E4A_VALIDATION_FAILED")


def test_bundled_schema_matches_normative_schema():
    """The schema shipped inside the implementation package (spec section 12:
    the schema ships with the implementation) must be the normative schema."""
    from importlib import resources

    bundled = json.loads(resources.files("e4a_sdk.schemas").joinpath("mandate-1.0.json").read_text())
    assert bundled == load_json(SCHEMA_PATH)
