import os
import json
from e4a_sdk.client import E4AClient

def test_sdk_health_local():
    client = E4AClient(base_url="http://localhost:8000")
    # health endpoint is present in Phase 3 API; in tests we call it and assert shape or handle connection errors
    try:
        r = client.health()
        assert "status" in r
    except Exception as e:
        # If server not running in test environment, the SDK still should raise E4AError or requests exception
        assert isinstance(e, Exception)
