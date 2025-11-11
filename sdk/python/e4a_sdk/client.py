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
    """
    The E4AClient provides a simple way to interact with the E4A API.
    """
    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 5):
        """
        Initializes the E4AClient.

        Args:
            base_url: The base URL of the E4A API.
            timeout: The timeout for HTTP requests in seconds.
        """
        self.base = base_url.rstrip("/")
        self.timeout = timeout

    def _post(self, path: str, json: Dict):
        """
        Sends a POST request to the E4A API.

        Args:
            path: The API endpoint path.
            json: The JSON payload to send.

        Returns:
            The JSON response from the API.

        Raises:
            E4AError: If the API returns an error.
        """
        url = f"{self.base}{path}"
        r = requests.post(url, json=json, timeout=self.timeout)
        if r.status_code >= 400:
            raise E4AError(f"HTTP {r.status_code}: {r.text}")
        return r.json()

    def _get(self, path: str):
        """
        Sends a GET request to the E4A API.

        Args:
            path: The API endpoint path.

        Returns:
            The JSON response from the API.

        Raises:
            E4AError: If the API returns an error.
        """
        url = f"{self.base}{path}"
        r = requests.get(url, timeout=self.timeout)
        if r.status_code >= 400:
            raise E4AError(f"HTTP {r.status_code}: {r.text}")
        return r.json()

    # High-level convenience methods:
    def create_mandate(self, issuer: str, beneficiary: str, amount: float, currency: str = "USD"):
        """
        Creates a new mandate.

        Args:
            issuer: The issuer of the mandate.
            beneficiary: The beneficiary of the mandate.
            amount: The amount of the mandate.
            currency: The currency of the mandate.

        Returns:
            The created mandate.
        """
        return self._post("/mandates/create", {"issuer": issuer,
                                               "beneficiary": beneficiary,
                                               "amount": amount,
                                               "currency": currency})

    def execute_mandate(self, mandate_id: str):
        """
        Executes a mandate.

        Args:
            mandate_id: The ID of the mandate to execute.

        Returns:
            The result of the mandate execution.
        """
        return self._post(f"/mandates/execute/{mandate_id}", {})

    def health(self):
        """
        Checks the health of the E4A API.

        Returns:
            The health status of the API.
        """
        return self._get("/health")

    def reputation(self):
        """
        Gets the reputation index.

        Returns:
            The reputation index.
        """
        return self._get("/reputation")
