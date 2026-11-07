"""Spec section 11 conformance: the HTTP API profile, exercised black-box
against a separately launched service process.

Expectations (status codes, stable error codes, the error envelope) are
taken from the section 11 table and section 14. Authentication behavior is
deployment-defined in 1.0, so the token tests assert only that an
unauthenticated caller is refused (401) when the deployment configures a
token — never that a specific code string is used for auth failures.
"""

from conftest import http_get, http_post, stop_service, vector_mandate


def _create(base_url, mandate, **kwargs):
    return http_post(base_url + "/v1/mandates", json=mandate, **kwargs)


def _envelope_code(response):
    body = response.json()
    assert set(body.keys()) == {"error"}, f"error response must be the spec envelope: {body}"
    assert set(body["error"].keys()) >= {"code", "message"}
    return body["error"]["code"]


def _gated_mandate(nonce):
    mandate = vector_mandate("valid-full.json")
    mandate.pop("mandate_id", None)
    mandate["replay_nonce"] = nonce
    return mandate


def test_create_get_execute_ungated(service):
    mandate = vector_mandate("valid-minimal.json")
    mandate["replay_nonce"] = "tck-api-1"
    created = _create(service.base_url, mandate)
    assert created.status_code == 201
    record = created.json()
    mandate_id = record["mandate_id"]

    fetched = http_get(f"{service.base_url}/v1/mandates/{mandate_id}")
    assert fetched.status_code == 200
    assert fetched.json()["mandate_id"] == mandate_id

    executed = http_post(f"{service.base_url}/v1/mandates/{mandate_id}/execute")
    assert executed.status_code == 200

    audit = http_get(f"{service.base_url}/v1/mandates/{mandate_id}/audit")
    assert audit.status_code == 200
    assert isinstance(audit.json(), list) and audit.json()

    missing = http_get(f"{service.base_url}/v1/mandates/no-such-id")
    assert missing.status_code == 404
    assert _envelope_code(missing) == "E4A_NOT_FOUND"


def test_validation_conflict_and_version_errors(service):
    invalid = vector_mandate("valid-minimal.json")
    del invalid["intent"]
    response = _create(service.base_url, invalid)
    assert response.status_code == 400
    assert _envelope_code(response) == "E4A_VALIDATION_FAILED"

    mandate = _gated_mandate("tck-api-2")
    assert _create(service.base_url, mandate).status_code == 201
    replay = _create(service.base_url, mandate)
    assert replay.status_code in (200, 201)  # spec 6: replay marker is implementation-chosen

    changed = dict(mandate, amount=999)
    conflict = _create(service.base_url, changed)
    assert conflict.status_code == 409
    assert _envelope_code(conflict) == "E4A_NONCE_CONFLICT"

    future = vector_mandate("valid-minimal.json")
    future["protocol_version"] = "99.0"
    future["replay_nonce"] = "tck-api-3"
    response = _create(service.base_url, future)
    assert response.status_code == 400
    assert _envelope_code(response) == "E4A_UNSUPPORTED_VERSION"


def test_decision_and_execution_error_mapping(service):
    created = _create(service.base_url, _gated_mandate("tck-api-4"))
    mandate_id = created.json()["mandate_id"]

    early = http_post(f"{service.base_url}/v1/mandates/{mandate_id}/execute")
    assert early.status_code == 409
    assert _envelope_code(early) == "E4A_APPROVAL_REQUIRED"

    stranger = http_post(
        f"{service.base_url}/v1/mandates/{mandate_id}/decisions",
        json={"actor": "did:ex:mallory", "decision": "approve"},
    )
    assert stranger.status_code == 403
    assert _envelope_code(stranger) == "E4A_UNAUTHORIZED_APPROVER"

    for actor in ("did:ex:carol", "did:ex:dave"):
        decided = http_post(
            f"{service.base_url}/v1/mandates/{mandate_id}/decisions",
            json={"actor": actor, "decision": "approve"},
        )
        assert decided.status_code == 200

    executed = http_post(f"{service.base_url}/v1/mandates/{mandate_id}/execute")
    assert executed.status_code == 200
    again = http_post(f"{service.base_url}/v1/mandates/{mandate_id}/execute")
    assert again.status_code == 409
    assert _envelope_code(again) == "E4A_INVALID_TRANSITION"

    missing_decision = http_post(
        f"{service.base_url}/v1/mandates/no-such-id/decisions",
        json={"actor": "did:ex:carol", "decision": "approve"},
    )
    assert missing_decision.status_code == 404
    assert _envelope_code(missing_decision) == "E4A_NOT_FOUND"


def test_persistence_across_service_restart(restartable_service):
    first = restartable_service()
    created = _create(first.base_url, _gated_mandate("tck-api-5"))
    mandate_id = created.json()["mandate_id"]
    stop_service(first)

    second = restartable_service()
    fetched = http_get(f"{second.base_url}/v1/mandates/{mandate_id}")
    assert fetched.status_code == 200
    assert fetched.json()["mandate_id"] == mandate_id


def test_configured_token_is_enforced(restartable_service):
    token = "tck" + "-test-" + "token"
    secured = restartable_service(api_token=token)
    refused = http_get(secured.base_url + "/v1/mandates/anything")
    assert refused.status_code == 401
    allowed = http_get(
        secured.base_url + "/v1/mandates/anything",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert allowed.status_code == 404  # authenticated; the mandate simply does not exist
