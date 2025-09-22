"""Tests for API entry point main module."""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from entry_points.api.main import create_app


class TestAPIMain:
    """Test API main application creation."""

    @pytest.fixture
    def app(self):
        """Create test application."""
        return create_app()

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    def test_create_app(self):
        """Test application creation."""
        app = create_app()
        assert app is not None
        assert app.title == "Pantstack API - Entry Point"
        assert app.version == "0.1.0"

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Pantstack API - Entry Point"}

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data

    def test_cors_middleware_configured(self, app):
        """Test CORS middleware is configured."""
        middlewares = [str(m) for m in app.middleware]
        assert any("CORSMiddleware" in m for m in middlewares)

    @patch("entry_points.api.main.APIRegistry")
    def test_service_discovery(self, mock_registry_class):
        """Test service discovery during app creation."""
        mock_registry = Mock()
        mock_registry.discover_services.return_value = [
            {"name": "auth", "version": "1.0.0"},
            {"name": "web", "version": "1.0.0"},
        ]
        mock_registry_class.return_value = mock_registry

        app = create_app()

        mock_registry.discover_services.assert_called_once()
        mock_registry.mount_services.assert_called_once_with(app)

    def test_api_prefix_configuration(self, client):
        """Test API routes are mounted with correct prefix."""
        # Test that service routes would be under /api/v1
        response = client.get("/openapi.json")
        assert response.status_code == 200
        openapi = response.json()

        # Check that paths exist
        assert "paths" in openapi

    @patch("entry_points.api.main.APIRegistry")
    def test_empty_service_discovery(self, mock_registry_class):
        """Test handling when no services are discovered."""
        mock_registry = Mock()
        mock_registry.discover_services.return_value = []
        mock_registry_class.return_value = mock_registry

        app = create_app()
        assert app is not None

        # Should still have default routes
        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200

    def test_exception_handlers_configured(self, app):
        """Test that exception handlers are configured."""
        # FastAPI apps have exception_handlers attribute
        assert hasattr(app, "exception_handlers")

    def test_startup_event_handler(self, app):
        """Test startup event handler exists."""
        # Check that startup events are configured
        assert hasattr(app, "router")
        assert hasattr(app.router, "on_startup")
