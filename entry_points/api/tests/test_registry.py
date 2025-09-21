"""Tests for API service registry."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import FastAPI, APIRouter
from pathlib import Path

from entry_points.api.registry import APIRegistry


class TestAPIRegistry:
    """Test API service registry."""

    @pytest.fixture
    def registry(self):
        """Create test registry."""
        return APIRegistry()

    def test_registry_initialization(self, registry):
        """Test registry initialization."""
        assert registry is not None
        assert hasattr(registry, "services_path")
        assert hasattr(registry, "services")

    @patch("entry_points.api.registry.Path")
    def test_discover_services_with_services(self, mock_path_class):
        """Test service discovery with available services."""
        # Mock directory structure
        mock_services_path = Mock()
        mock_path_class.return_value = mock_services_path
        mock_services_path.exists.return_value = True

        # Mock service directories
        mock_auth_dir = Mock()
        mock_auth_dir.is_dir.return_value = True
        mock_auth_dir.name = "auth"

        mock_web_dir = Mock()
        mock_web_dir.is_dir.return_value = True
        mock_web_dir.name = "web"

        mock_services_path.iterdir.return_value = [mock_auth_dir, mock_web_dir]

        # Mock module existence
        with patch("entry_points.api.registry.importlib.util.find_spec") as mock_find_spec:
            mock_find_spec.return_value = Mock()  # Module exists

            registry = APIRegistry()
            manifests = registry.discover_services()

            assert len(manifests) == 2
            assert any(m["name"] == "auth" for m in manifests)
            assert any(m["name"] == "web" for m in manifests)

    @patch("entry_points.api.registry.Path")
    def test_discover_services_no_services_dir(self, mock_path_class):
        """Test service discovery when services directory doesn't exist."""
        mock_services_path = Mock()
        mock_path_class.return_value = mock_services_path
        mock_services_path.exists.return_value = False

        registry = APIRegistry()
        manifests = registry.discover_services()

        assert manifests == []

    def test_mount_services(self, registry):
        """Test mounting services to FastAPI app."""
        app = FastAPI()

        # Mock a service with router
        mock_router = APIRouter()
        mock_router.add_api_route("/test", lambda: {"test": "response"})

        mock_service = Mock()
        mock_service.router = mock_router

        registry.services = {"test_service": mock_service}

        registry.mount_services(app)

        # Check that routes were added
        routes = [route.path for route in app.routes]
        assert any("/api/v1/test_service/test" in str(route) for route in routes)

    def test_mount_services_with_no_router(self, registry):
        """Test mounting service without router attribute."""
        app = FastAPI()

        # Mock a service without router
        mock_service = Mock(spec=[])  # No router attribute
        registry.services = {"test_service": mock_service}

        # Should not raise error
        registry.mount_services(app)

    @patch("entry_points.api.registry.importlib.import_module")
    def test_import_service_module(self, mock_import_module):
        """Test importing service module."""
        mock_module = Mock()
        mock_module.router = APIRouter()
        mock_import_module.return_value = mock_module

        registry = APIRegistry()
        result = registry._import_service_module("test_service")

        assert result is not None
        assert hasattr(result, "router")
        mock_import_module.assert_called_once_with("services.test_service.app.api")

    @patch("entry_points.api.registry.importlib.import_module")
    def test_import_service_module_failure(self, mock_import_module):
        """Test handling of import failure."""
        mock_import_module.side_effect = ImportError("Module not found")

        registry = APIRegistry()
        result = registry._import_service_module("test_service")

        assert result is None

    def test_get_service_manifest(self, registry):
        """Test getting service manifest."""
        # Mock a service with metadata
        mock_service = Mock()
        mock_service.__version__ = "1.0.0"
        mock_service.__doc__ = "Test service"

        manifest = registry._get_service_manifest("test_service", mock_service)

        assert manifest["name"] == "test_service"
        assert manifest["version"] == "1.0.0"
        assert manifest["description"] == "Test service"
        assert manifest["status"] == "loaded"

    def test_get_service_manifest_defaults(self, registry):
        """Test service manifest with default values."""
        mock_service = Mock(spec=[])  # No special attributes

        manifest = registry._get_service_manifest("test_service", mock_service)

        assert manifest["name"] == "test_service"
        assert manifest["version"] == "0.1.0"
        assert manifest["description"] == "test_service service"
        assert manifest["status"] == "loaded"

    def test_health_check(self, registry):
        """Test health check method."""
        registry.services = {
            "auth": Mock(),
            "web": Mock()
        }

        health = registry.health_check()

        assert health["status"] == "healthy"
        assert health["services"]["auth"] == "loaded"
        assert health["services"]["web"] == "loaded"
        assert health["total_services"] == 2

    def test_health_check_no_services(self, registry):
        """Test health check with no services."""
        registry.services = {}

        health = registry.health_check()

        assert health["status"] == "healthy"
        assert health["services"] == {}
        assert health["total_services"] == 0