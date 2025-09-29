"""Performance tests for the Research service."""

import time
from concurrent.futures import ThreadPoolExecutor
import pytest

from app.main import create_app
from fastapi.testclient import TestClient


class TestHealthEndpointPerformance:
    """Performance tests for the health endpoint."""

    def test_health_endpoint_response_time(self, client):
        """Test that health endpoint responds within acceptable time."""
        start_time = time.perf_counter()
        response = client.get("/health")
        end_time = time.perf_counter()

        response_time = end_time - start_time

        assert response.status_code == 200
        assert response_time < 0.1  # Should respond within 100ms

    @pytest.mark.performance
    def test_health_endpoint_concurrent_requests(self, client):
        """Test health endpoint under concurrent load."""
        def make_request():
            response = client.get("/health")
            assert response.status_code == 200
            return response.json()

        # Test with 10 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in futures]

        # All requests should succeed
        assert len(results) == 10
        for result in results:
            assert result["status"] == "ok"

    @pytest.mark.performance
    @pytest.mark.benchmark
    def test_health_endpoint_benchmark(self, request):
        """Benchmark the health endpoint using pytest-benchmark."""
        app = create_app()
        client = TestClient(app)

        def health_request():
            response = client.get("/health")
            assert response.status_code == 200
            return response.json()

        if not request.config.pluginmanager.hasplugin("benchmark"):
            pytest.skip("pytest-benchmark plugin not installed")
        benchmark = request.getfixturevalue("benchmark")
        # Benchmark the function
        result = benchmark(health_request)
        assert result["status"] == "ok"

    def test_app_startup_time(self):
        """Test that app startup time is reasonable."""
        start_time = time.perf_counter()
        app = create_app()
        TestClient(app)  # This triggers app startup
        end_time = time.perf_counter()

        startup_time = end_time - start_time
        assert startup_time < 1.0  # Should start up within 1 second

    @pytest.mark.performance
    def test_memory_usage_under_load(self, client):
        """Test that memory usage remains stable under load."""
        psutil = pytest.importorskip("psutil")
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Make 100 requests
        for _ in range(100):
            response = client.get("/health")
            assert response.status_code == 200

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 10MB)
        assert memory_increase < 10 * 1024 * 1024


class TestApplicationPerformance:
    """Overall application performance tests."""

    @pytest.mark.performance
    def test_application_handles_rapid_requests(self, client):
        """Test that application handles rapid sequential requests."""
        start_time = time.perf_counter()

        for _ in range(50):
            response = client.get("/health")
            assert response.status_code == 200

        end_time = time.perf_counter()
        total_time = end_time - start_time

        # Should handle 50 requests in less than 5 seconds
        assert total_time < 5.0
        # Average response time should be less than 100ms
        average_response_time = total_time / 50
        assert average_response_time < 0.1

    @pytest.mark.performance
    def test_concurrent_different_endpoints(self, client):
        """Test performance with concurrent requests to different endpoints."""
        def make_health_request():
            return client.get("/health")

        def make_404_request():
            return client.get("/nonexistent")

        with ThreadPoolExecutor(max_workers=6) as executor:
            # Mix of successful and 404 requests
            futures = []
            futures.extend([executor.submit(make_health_request) for _ in range(3)])
            futures.extend([executor.submit(make_404_request) for _ in range(3)])

            results = [future.result() for future in futures]

        # Check that we got expected status codes
        status_codes = [r.status_code for r in results]
        assert status_codes.count(200) == 3  # Health requests
        assert status_codes.count(404) == 3  # 404 requests

    @pytest.mark.slow
    @pytest.mark.performance
    def test_sustained_load(self, client):
        """Test application under sustained load."""
        import httpx

        duration = 5  # Run for 5 seconds
        start_time = time.perf_counter()
        request_count = 0
        errors = 0

        while time.perf_counter() - start_time < duration:
            try:
                response = client.get("/health")
                if response.status_code == 200:
                    request_count += 1
                else:
                    errors += 1
            except httpx.HTTPError:
                errors += 1

        end_time = time.perf_counter()
        actual_duration = end_time - start_time
        requests_per_second = request_count / actual_duration

        # Should handle at least 10 requests per second with minimal errors
        assert requests_per_second >= 10
        assert errors < request_count * 0.01  # Less than 1% error rate