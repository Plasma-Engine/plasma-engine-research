"""Integration-style tests verifying the health endpoint.

The tests serve as executable documentation demonstrating how to exercise the
FastAPI app with the HTTPX test client.
"""

import pytest
from fastapi.testclient import TestClient

from app.config import ResearchSettings


@pytest.mark.parametrize("method", ["get", "head"])
def test_health_endpoint_reports_ok_status(client: TestClient, test_settings: ResearchSettings, method: str) -> None:
    """The /health route should always return a 200 response with service name."""

    response = getattr(client, method)("/health")

    assert response.status_code == 200
    if method == "get":
        payload = response.json()
        assert payload["status"] == "ok"
        assert payload["service"] == test_settings.app_name

