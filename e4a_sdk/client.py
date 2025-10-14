# e4a_sdk/client.py
"""
Minimal E4A SDK: wraps HTTP to the local API (or can be subclassed for in-process usage).
Designed to be dependency-light (uses requests).
"""
import requests
from typing import Dict


class E4AError(Exception):
    pass


class E4AClient:
    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 5):
        self.base = base_url.rstrip("/")
        self.timeout = timeout

    def _post(self, path: str, json: Dict):
        url = f"{self.base}{path}"
        r = requests.post(url, json=json, timeout=self.timeout)
        if r.status_code >= 400:
            raise E4AError(f"HTTP {r.status_code}: {r.text}")
        return r.json()

    def _get(self, path: str):
        url = f"{self.base}{path}"
        r = requests.get(url, timeout=self.timeout)
        if r.status_code >= 400:
            raise E4AError(f"HTTP {r.status_code}: {r.text}")
        return r.json()

    # High-level convenience methods:
    def create_mandate(self, issuer: str, beneficiary: str, amount: float, currency: str = "USD"):
        return self._post("/mandates/create", {"issuer": issuer,
                                               "beneficiary": beneficiary,
                                               "amount": amount,
                                               "currency": currency})

    def execute_mandate(self, mandate_id: str):
        return self._post(f"/mandates/execute/{mandate_id}", {})

    def health(self):
        return self._get("/health")

    def reputation(self):
        return self._get("/reputation")
