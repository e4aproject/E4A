from sdk.python.e4a_sdk.scribe_agent import ScribeAgent
from sdk.python.e4a_sdk.mandate_engine import MandateEngine


def test_create_and_execute_mandate(tmp_path):
    # use temp mission log
    log = tmp_path / "mission_log.jsonl"
    s = ScribeAgent(log_path=str(log))
    me = MandateEngine(scribe=s)
    m = me.create_mandate({
        "issuer": "did:ex:alice",
        "beneficiary": "did:ex:bob",
        "amount": 50,
        "currency": "USD",
        "fee_distribution": {"protocol": 0.02, "validator": 0.01, "issuer": 0},
        "intent": {
            "goal": "create and execute a simple mandate",
            "expected_outcome": "mandate executed and logged",
            "contextual_tone": "neutral",
            "statistical_purpose": "validate mandate engine functionality"
        }
    })
    assert m['issuer'] == "did:ex:alice"
    assert 'mandate_id' in m
    res = me.execute_mandate(m['mandate_id'])
    assert res['status'] == 'executed'
    assert 'fees' in res
    # check log lines
    lines = open(log, 'r').read().strip().splitlines()
    assert any('mandate_created' in ln for ln in lines)
    assert any('mandate_executed' in ln for ln in lines)
