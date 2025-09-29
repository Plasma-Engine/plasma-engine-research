"""Integration-style tests verifying the health endpoint.

The tests serve as executable documentation demonstrating how to exercise the
FastAPI app with the HTTPX test client.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture()
def client() -> TestClient:
    """Provide a TestClient backed by the default application settings."""

    app = create_app()
    return TestClient(app)


def test_health_endpoint_reports_ok_status(client: TestClient) -> None:
    """The /health route should always return a 200 response with service name."""

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "plasma-engine-research"

