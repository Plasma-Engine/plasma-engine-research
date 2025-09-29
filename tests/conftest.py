"""Local test configuration for the Research service."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# -- Path management ------------------------------------------------------
# Ensure ``import app`` keeps working even when pytest is executed from clean
# environments (local venvs, CI runners) where only ``src/`` gets added to
# ``sys.path`` by editable installs. The research service retains the FastAPI
# app inside ``app/`` so we insert the repository root explicitly.
SERVICE_ROOT = Path(__file__).resolve().parent.parent
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from app.config import ResearchSettings  # noqa: E402
from app.main import create_app  # noqa: E402


@pytest.fixture
def test_settings():
    """Provide test-specific settings."""
    return ResearchSettings(
        app_name="plasma-engine-research-test",
        cors_origins=["http://localhost:3000", "http://localhost:8000"],
        openai_api_key="test-key-123"
    )


@pytest.fixture
def app(test_settings):
    """Create FastAPI app with test settings."""
    return create_app(test_settings)


@pytest.fixture
def client(app):
    """Provide TestClient for the research service."""
    return TestClient(app)