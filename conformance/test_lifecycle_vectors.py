"""Spec sections 4-8 conformance: the lifecycle vectors L1-L8.

The vectors in docs/protocol/test-vectors/lifecycle-vectors.json are
interpreted generically: each step performs an operation (create, decide,
execute, get) against a fresh implementation and asserts the expected
lifecycle state or the expected spec section 14 error code, including that
an error step leaves the state unchanged where the vector says so.
"""

import json

import pytest

from conftest import VECTORS_DIR, error_code, load_json, state_of

LIFECYCLE = load_json(VECTORS_DIR / "lifecycle-vectors.json")["vectors"]


def _body_for(step):
    if "body" in step:
        return json.loads(json.dumps(step["body"]))
    mandate = load_json(VECTORS_DIR / step["body_ref"])["mandate"]
    mandate = json.loads(json.dumps(mandate))
    mandate.pop("mandate_id", None)
    for key, value in step.get("mutate", {}).items():
        mandate[key] = value
    return mandate


@pytest.mark.parametrize("vector", LIFECYCLE, ids=[v["id"] for v in LIFECYCLE])
def test_lifecycle_vector(engine, vector):
    mandate_id = None
    first_created = None
    for step in vector["steps"]:
        op = step["op"]
        if op == "create":
            body = _body_for(step)
            if "expect_error" in step:
                with pytest.raises(Exception) as excinfo:
                    engine.create_mandate(body)
                assert error_code(excinfo.value) == step["expect_error"]
                continue
            created = engine.create_mandate(body)
            mandate_id = created["mandate_id"]
            if step.get("capture_id"):
                first_created = mandate_id
            if step.get("expect") == "same_record_as_step_1":
                assert mandate_id == first_created
            if "expect_state" in step:
                # Assert on the create result itself: a later retrieval may
                # legitimately surface a time-driven transition (spec 5).
                assert state_of(created) == step["expect_state"]
        elif op == "decide":
            if "expect_error" in step:
                with pytest.raises(Exception) as excinfo:
                    engine.record_decision(mandate_id, step["actor"], step["decision"])
                assert error_code(excinfo.value) == step["expect_error"]
            else:
                engine.record_decision(mandate_id, step["actor"], step["decision"])
            if "expect_state" in step:
                assert state_of(engine.get_mandate(mandate_id)) == step["expect_state"]
        elif op == "execute":
            target = step.get("id", mandate_id)
            if "expect_error" in step:
                with pytest.raises(Exception) as excinfo:
                    engine.execute_mandate(target)
                assert error_code(excinfo.value) == step["expect_error"]
            else:
                result = engine.execute_mandate(target)
                if "expect_state" in step:
                    assert state_of(result) == step["expect_state"]
        elif op == "get":
            target = step.get("id", mandate_id)
            if "expect_error" in step:
                with pytest.raises(Exception) as excinfo:
                    engine.get_mandate(target)
                assert error_code(excinfo.value) == step["expect_error"]
            else:
                record = engine.get_mandate(target)
                assert record["mandate_id"] == target
        else:  # pragma: no cover - guards the vectors themselves
            raise AssertionError(f"unknown op in vector {vector['id']}: {op}")
