"""Comprehensive tests for the main FastAPI application."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import create_app
from app.config import ResearchSettings


class TestCreateApp:
    """Test the create_app factory function."""

    def test_creates_fastapi_instance(self):
        """Test that create_app returns a FastAPI instance."""
        app = create_app()
        assert isinstance(app, FastAPI)

    def test_app_title_from_settings(self, test_settings):
        """Test that app title is set from settings."""
        app = create_app(test_settings)
        assert app.title == test_settings.app_name

    def test_app_with_custom_settings(self):
        """Test app creation with custom settings."""
        custom_settings = ResearchSettings(
            app_name="custom-research-service",
            cors_origins=["https://custom.com"],
            openai_api_key="custom-key"
        )
        app = create_app(custom_settings)
        assert app.title == "custom-research-service"

    def test_app_with_default_settings(self):
        """Test app creation with default settings when none provided."""
        with patch('app.main.get_settings') as mock_get_settings:
            mock_settings = ResearchSettings()
            mock_get_settings.return_value = mock_settings

            app = create_app()
            assert app.title == mock_settings.app_name

    def test_cors_middleware_configured(self, test_settings):
        """Test that CORS middleware is properly configured."""
        app = create_app(test_settings)

        # Check that middleware is added (FastAPI doesn't expose middleware config easily)
        # We'll test this through the actual client
        client = TestClient(app)

        response = client.options("/health", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        })

        # Should not be rejected due to CORS
        assert response.status_code != 403


class TestHealthEndpoint:
    """Test the health check endpoint."""

    def test_health_endpoint_returns_ok_status(self, client):
        """Test that health endpoint returns 200 with correct structure."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "service" in data

    def test_health_endpoint_service_name(self, client, test_settings):
        """Test that health endpoint returns correct service name."""
        response = client.get("/health")
        data = response.json()

        assert data["service"] == test_settings.app_name

    def test_health_endpoint_content_type(self, client):
        """Test that health endpoint returns JSON content type."""
        response = client.get("/health")

        assert response.headers["content-type"] == "application/json"

    def test_health_endpoint_no_auth_required(self, client):
        """Test that health endpoint doesn't require authentication."""
        # Health endpoints should be publicly accessible
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_endpoint_tags(self, app):
        """Test that health endpoint has correct OpenAPI tags."""
        # Check that the health endpoint is tagged properly
        routes = [route for route in app.routes if hasattr(route, 'path') and route.path == '/health']
        assert len(routes) == 1

        route = routes[0]
        assert hasattr(route, 'tags')
        assert 'health' in route.tags


class TestCORSConfiguration:
    """Test CORS middleware configuration and behavior."""

    def test_cors_allows_configured_origins(self, test_settings):
        """Test that CORS allows configured origins."""
        app = create_app(test_settings)
        client = TestClient(app)

        for origin in test_settings.cors_origins:
            response = client.get("/health", headers={"Origin": origin})
            assert response.status_code == 200

    def test_cors_preflight_request(self, client):
        """Test CORS preflight OPTIONS request."""
        response = client.options("/health", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "content-type"
        })

        # Should handle preflight request
        assert response.status_code in [200, 204]

    def test_cors_headers_present(self, client):
        """Test that CORS headers are present in response."""
        response = client.get("/health", headers={
            "Origin": "http://localhost:3000"
        })

        # Should include CORS headers
        assert "access-control-allow-origin" in response.headers


class TestApplicationIntegration:
    """Integration tests for the complete application."""

    def test_app_startup_and_shutdown(self):
        """Test that app can start up and shut down cleanly."""
        app = create_app()
        client = TestClient(app)

        # Test that we can make requests
        response = client.get("/health")
        assert response.status_code == 200

        # TestClient handles cleanup automatically

    def test_app_handles_404(self, client):
        """Test that app properly handles 404 errors."""
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404

    def test_app_handles_405_method_not_allowed(self, client):
        """Test that app properly handles method not allowed."""
        response = client.post("/health")  # Health only supports GET
        assert response.status_code == 405

    def test_multiple_requests_to_same_endpoint(self, client):
        """Test that multiple requests to same endpoint work."""
        for _ in range(3):
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"

    @pytest.mark.parametrize("method", ["GET", "HEAD"])
    def test_health_supports_multiple_methods(self, client, method):
        """Test that health endpoint supports GET and HEAD methods."""
        if method == "HEAD":
            response = client.head("/health")
            assert response.status_code == 200
            assert response.content == b""  # HEAD should not return body
        else:
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "ok"