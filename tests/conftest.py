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

from app.config import ResearchSettings
from app.main import create_app


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


@pytest.fixture
def mock_research_query():
    """Provide a mock research query."""
    return {
        "query": "What are the latest developments in quantum computing?",
        "max_results": 10,
        "include_summary": True
    }


@pytest.fixture
def mock_research_results():
    """Provide mock research results."""
    return {
        "query": "quantum computing developments",
        "results": [
            {
                "title": "Quantum Computing Breakthrough 2024",
                "summary": "Major advancement in quantum error correction",
                "url": "https://example.com/quantum-2024",
                "relevance_score": 0.95,
                "published_date": "2024-01-15T10:30:00Z",
                "source": "Nature Quantum Information"
            },
            {
                "title": "New Quantum Architecture",
                "summary": "Revolutionary approach to quantum processing",
                "url": "https://example.com/quantum-arch",
                "relevance_score": 0.87,
                "published_date": "2024-01-10T14:20:00Z",
                "source": "Physical Review Letters"
            }
        ],
        "total_results": 2,
        "search_time": 1.23,
        "confidence": 0.89
    }