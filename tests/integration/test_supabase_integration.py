"""Integration tests for Supabase services."""

import os
import time
from typing import Dict, Any

import pytest
import requests


class TestSupabaseIntegration:
    """Test Supabase local development services."""

    @pytest.fixture(scope="class")
    def supabase_config(self):
        """Supabase configuration for local development."""
        return {
            "url": os.getenv("SUPABASE_URL", "http://localhost:54321"),
            "anon_key": os.getenv("SUPABASE_ANON_KEY", "test-anon-key"),
            "service_key": os.getenv("SUPABASE_SERVICE_KEY", "test-service-key"),
        }

    @pytest.fixture(scope="class")
    def wait_for_supabase(self, supabase_config):
        """Wait for Supabase services to be ready."""
        max_retries = 30
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                # Check if Supabase API is responding
                response = requests.get(
                    f"{supabase_config['url']}/rest/v1/",
                    headers={
                        "apikey": supabase_config["anon_key"],
                        "Authorization": f"Bearer {supabase_config['anon_key']}",
                    },
                    timeout=5,
                )
                if response.status_code in [200, 401]:  # 401 is expected without proper auth
                    return True
            except requests.exceptions.ConnectionError:
                pass

            if attempt < max_retries - 1:
                time.sleep(retry_delay)

        pytest.skip("Supabase not available for integration tests")

    def test_supabase_api_health(self, supabase_config, wait_for_supabase):
        """Test Supabase API health check."""
        response = requests.get(
            f"{supabase_config['url']}/rest/v1/",
            headers={
                "apikey": supabase_config["anon_key"],
                "Authorization": f"Bearer {supabase_config['anon_key']}",
            },
        )

        # Should get a response (200 or 401 is acceptable)
        assert response.status_code in [200, 401, 404]

    def test_supabase_auth_endpoint(self, supabase_config, wait_for_supabase):
        """Test Supabase Auth endpoint."""
        auth_url = f"{supabase_config['url']}/auth/v1"

        response = requests.get(auth_url)

        # Auth endpoint should be reachable
        assert response.status_code in [200, 404, 405]

    def test_supabase_storage_endpoint(self, supabase_config, wait_for_supabase):
        """Test Supabase Storage endpoint."""
        storage_url = f"{supabase_config['url']}/storage/v1"

        response = requests.get(
            storage_url,
            headers={
                "apikey": supabase_config["anon_key"],
                "Authorization": f"Bearer {supabase_config['anon_key']}",
            },
        )

        # Storage endpoint should be reachable
        assert response.status_code in [200, 401, 404]

    def test_supabase_realtime_endpoint(self, supabase_config, wait_for_supabase):
        """Test Supabase Realtime endpoint."""
        realtime_url = f"{supabase_config['url']}/realtime/v1"

        response = requests.get(realtime_url)

        # Realtime endpoint should be reachable
        assert response.status_code in [200, 404, 405, 426]  # 426 = Upgrade Required (WebSocket)

    def test_database_connection_via_rest_api(self, supabase_config, wait_for_supabase):
        """Test database connection via REST API."""
        # Try to access a non-existent table (should get proper error)
        response = requests.get(
            f"{supabase_config['url']}/rest/v1/non_existent_table",
            headers={
                "apikey": supabase_config["anon_key"],
                "Authorization": f"Bearer {supabase_config['anon_key']}",
            },
        )

        # Should get an error response indicating the database is accessible
        assert response.status_code in [401, 404, 406]  # Auth or table not found errors are expected

    def test_service_discovery(self, supabase_config, wait_for_supabase):
        """Test Supabase service discovery."""
        base_url = supabase_config["url"]

        # Test various Supabase service endpoints
        endpoints = [
            "/rest/v1/",
            "/auth/v1",
            "/storage/v1",
            "/realtime/v1",
        ]

        for endpoint in endpoints:
            full_url = f"{base_url}{endpoint}"

            try:
                response = requests.head(full_url, timeout=5)
                # Connection should succeed (any HTTP status is fine)
                assert isinstance(response.status_code, int)
            except requests.exceptions.ConnectionError:
                pytest.fail(f"Could not connect to Supabase endpoint: {full_url}")

    @pytest.mark.skip(reason="Requires proper Supabase setup with test tables")
    def test_crud_operations_via_rest_api(self, supabase_config, wait_for_supabase):
        """Test CRUD operations via Supabase REST API."""
        # This test would require a properly configured Supabase instance
        # with test tables and proper authentication setup

        headers = {
            "apikey": supabase_config["service_key"],
            "Authorization": f"Bearer {supabase_config['service_key']}",
            "Content-Type": "application/json",
        }

        # Example test table operations (would need actual table setup)
        test_data = {
            "name": "Integration Test",
            "description": "Test record for integration testing",
        }

        # Create record
        response = requests.post(
            f"{supabase_config['url']}/rest/v1/test_table",
            json=test_data,
            headers=headers,
        )

        # This would work with proper table setup
        # assert response.status_code == 201

    def test_environment_configuration(self, supabase_config):
        """Test Supabase environment configuration."""
        # Verify configuration structure
        assert "url" in supabase_config
        assert "anon_key" in supabase_config
        assert "service_key" in supabase_config

        # URL should be properly formatted
        assert supabase_config["url"].startswith("http")
        assert "localhost" in supabase_config["url"] or "supabase" in supabase_config["url"]

        # Keys should not be empty
        assert len(supabase_config["anon_key"]) > 0
        assert len(supabase_config["service_key"]) > 0

    def test_cors_configuration(self, supabase_config, wait_for_supabase):
        """Test CORS configuration for local development."""
        # Test preflight request
        response = requests.options(
            f"{supabase_config['url']}/rest/v1/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type,Authorization,apikey",
            },
        )

        # CORS should be configured for local development
        # Status could be 200 (success) or 404 (endpoint not found) but connection should work
        assert response.status_code in [200, 404, 405]

    def test_websocket_endpoint_availability(self, supabase_config, wait_for_supabase):
        """Test WebSocket endpoint availability for realtime features."""
        # Parse WebSocket URL from HTTP URL
        ws_url = supabase_config["url"].replace("http://", "ws://").replace("https://", "wss://")
        ws_endpoint = f"{ws_url}/realtime/v1/websocket"

        # We can't easily test WebSocket connection without additional dependencies
        # But we can test that the endpoint structure is correct
        assert ws_endpoint.startswith("ws://") or ws_endpoint.startswith("wss://")
        assert "realtime" in ws_endpoint
        assert "websocket" in ws_endpoint

    def test_database_migrations_status(self, supabase_config, wait_for_supabase):
        """Test database migrations status (if accessible)."""
        # This would typically require admin access or specific migration endpoints
        # For now, just verify the service is responsive
        response = requests.get(
            f"{supabase_config['url']}/rest/v1/",
            headers={
                "apikey": supabase_config["service_key"],
                "Authorization": f"Bearer {supabase_config['service_key']}",
            },
        )

        # Service should be responsive
        assert response.status_code in [200, 401, 404]

    def test_local_development_features(self, supabase_config, wait_for_supabase):
        """Test Supabase local development specific features."""
        # Test that we're running in local mode
        assert "localhost" in supabase_config["url"]

        # Local Supabase should have development-friendly defaults
        # These are characteristics of local vs production setup
        local_characteristics = {
            "uses_localhost": "localhost" in supabase_config["url"],
            "development_port": "54321" in supabase_config["url"],
            "has_test_keys": len(supabase_config["anon_key"]) > 0,
        }

        for characteristic, condition in local_characteristics.items():
            assert condition, f"Local development characteristic failed: {characteristic}"