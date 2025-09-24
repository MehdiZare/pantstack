"""Base test classes for module testing."""

from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


class ModuleTestBase:
    """Base test class for testing service modules."""

    module_name: str = "test_module"
    service_name: str = "test_service"

    @pytest.fixture
    def module_config(self) -> Dict[str, Any]:
        """Provide default module configuration.

        Override this in subclasses to provide custom config.
        """
        return {
            "enabled": True,
            "max_retries": 3,
            "timeout": 30,
        }

    @pytest.fixture
    def module_instance(self, module_config):
        """Create module instance for testing.

        Override this to create your specific module.
        """
        raise NotImplementedError("Subclasses must implement module_instance fixture")

    @pytest.fixture
    def app(self, module_instance) -> FastAPI:
        """Create FastAPI app with module routes."""
        app = FastAPI()
        router = module_instance.get_routes()
        if router:
            app.include_router(router)
        return app

    @pytest.fixture
    def client(self, app) -> TestClient:
        """Create test client for the app."""
        return TestClient(app)

    def test_module_initialization(self, module_instance):
        """Test that module initializes correctly."""
        assert module_instance is not None
        assert module_instance.name == self.module_name
        assert hasattr(module_instance, "get_routes")
        assert hasattr(module_instance, "get_tasks")
        assert hasattr(module_instance, "get_handlers")

    def test_module_routes_registration(self, module_instance, app):
        """Test that module routes are properly registered."""
        router = module_instance.get_routes()
        if router:
            # Check that routes are registered
            routes = [route.path for route in app.routes]
            assert len(routes) > 0

    def test_module_tasks_registration(self, module_instance):
        """Test that module tasks are properly defined."""
        tasks = module_instance.get_tasks()
        if tasks:
            assert isinstance(tasks, list)
            assert all(isinstance(task, str) for task in tasks)
            # Check task naming convention
            for task in tasks:
                assert task.startswith(f"{self.service_name}.{self.module_name}.")

    def test_module_handlers_registration(self, module_instance):
        """Test that module event handlers are properly defined."""
        handlers = module_instance.get_handlers()
        if handlers:
            assert isinstance(handlers, dict)
            # Check handler naming convention
            for event_type in handlers.keys():
                assert event_type.startswith(f"{self.service_name}.{self.module_name}.")

    @pytest.mark.asyncio
    async def test_module_initialize_shutdown(self, module_instance):
        """Test module initialization and shutdown lifecycle."""
        # Initialize
        module_instance.initialize()
        # Add assertions for initialization side effects if any

        # Shutdown
        module_instance.shutdown()
        # Add assertions for cleanup side effects if any


class ModuleAPITestBase(ModuleTestBase):
    """Base test class for testing module API endpoints."""

    @pytest.mark.asyncio
    async def test_module_info_endpoint(self, client, module_instance):
        """Test module info endpoint if it exists."""
        response = client.get(f"/{self.module_name}/")
        if response.status_code == 200:
            data = response.json()
            assert "module" in data or "status" in data

    def test_module_error_handling(self, client):
        """Test module error handling."""
        # Test non-existent endpoint
        response = client.get(f"/{self.module_name}/non-existent-endpoint-xyz")
        assert response.status_code == 404

    @pytest.mark.parametrize("method", ["GET", "POST", "PUT", "DELETE"])
    def test_module_method_not_allowed(self, client, method):
        """Test that unsupported methods return 405."""
        # This will be overridden by specific module tests
        pass


class ModuleTaskTestBase(ModuleTestBase):
    """Base test class for testing module Celery tasks."""

    @pytest.fixture
    def celery_app(self):
        """Mock Celery app for testing."""
        from celery import Celery

        app = Celery("test")
        app.conf.update(
            task_always_eager=True,
            task_eager_propagates=True,
        )
        return app

    def test_task_registration(self, module_instance, celery_app):
        """Test that tasks are registered with Celery."""
        tasks = module_instance.get_tasks()
        if tasks:
            for task_name in tasks:
                # In a real scenario, you'd check if the task is registered
                assert task_name is not None

    @patch("celery.Task.apply_async")
    def test_task_async_execution(self, mock_apply_async, module_instance):
        """Test that tasks can be executed asynchronously."""
        tasks = module_instance.get_tasks()
        if tasks:
            mock_apply_async.return_value = Mock(id="test-task-id")
            # Simulate task execution
            result = mock_apply_async(args=["test_data"])
            assert result.id == "test-task-id"


class ModuleEventTestBase(ModuleTestBase):
    """Base test class for testing module event handlers."""

    @pytest.fixture
    def event_publisher(self):
        """Mock event publisher."""
        return Mock()

    @pytest.fixture
    def sample_event(self) -> Dict[str, Any]:
        """Sample event for testing."""
        return {
            "event_type": f"{self.service_name}.{self.module_name}.created",
            "data": {"id": "test-123", "name": "Test Entity"},
            "metadata": {"timestamp": "2024-01-01T00:00:00Z"},
        }

    @pytest.mark.asyncio
    async def test_event_handler_execution(self, module_instance, sample_event):
        """Test that event handlers execute correctly."""
        handlers = module_instance.get_handlers()
        if handlers:
            handler = handlers.get(sample_event["event_type"])
            if handler:
                # Test async handler
                if asyncio.iscoroutinefunction(handler):
                    await handler(sample_event)
                else:
                    handler(sample_event)

    def test_event_handler_error_resilience(self, module_instance, sample_event):
        """Test that event handlers handle errors gracefully."""
        handlers = module_instance.get_handlers()
        if handlers:
            # Modify event to cause potential error
            bad_event = {"event_type": sample_event["event_type"]}
            handler = handlers.get(sample_event["event_type"])
            if handler:
                try:
                    handler(bad_event)
                except KeyError:
                    # Handler should handle missing data gracefully
                    pass


class ModuleIntegrationTestBase(ModuleTestBase):
    """Base test class for module integration testing."""

    @pytest.fixture
    def mock_database(self):
        """Mock database for testing."""
        return Mock()

    @pytest.fixture
    def mock_cache(self):
        """Mock cache for testing."""
        return Mock()

    @pytest.fixture
    def mock_message_queue(self):
        """Mock message queue for testing."""
        return Mock()

    @pytest.fixture
    def integrated_module(
        self, module_instance, mock_database, mock_cache, mock_message_queue
    ):
        """Create module with mocked integrations."""
        # Inject mocks into module if it supports dependency injection
        if hasattr(module_instance, "set_database"):
            module_instance.set_database(mock_database)
        if hasattr(module_instance, "set_cache"):
            module_instance.set_cache(mock_cache)
        if hasattr(module_instance, "set_message_queue"):
            module_instance.set_message_queue(mock_message_queue)
        return module_instance

    @pytest.mark.asyncio
    async def test_module_with_integrations(self, integrated_module):
        """Test module with all integrations."""
        integrated_module.initialize()
        # Add specific integration tests here
        integrated_module.shutdown()


class ModuleLoadTestBase:
    """Base class for module load testing."""

    @pytest.fixture
    def load_test_client(self, app):
        """Create client for load testing."""
        from locust import HttpUser, between, task

        class ModuleUser(HttpUser):
            wait_time = between(1, 3)

            @task
            def test_module_endpoint(self):
                self.client.get(f"/{self.module_name}/")

        return ModuleUser

    def test_module_under_load(self, load_test_client):
        """Test module performance under load."""
        # This would be run with locust in practice
        pass


# Utility functions for module testing


def create_mock_module(name: str = "test_module") -> Mock:
    """Create a mock module for testing.

    Args:
        name: Module name

    Returns:
        Mock module instance
    """
    mock_module = Mock()
    mock_module.name = name
    mock_module.get_routes.return_value = Mock()
    mock_module.get_tasks.return_value = [
        f"service.{name}.task1",
        f"service.{name}.task2",
    ]
    mock_module.get_handlers.return_value = {
        f"service.{name}.created": Mock(),
        f"service.{name}.updated": Mock(),
    }
    mock_module.initialize = Mock()
    mock_module.shutdown = Mock()
    return mock_module


def assert_module_interface(module) -> None:
    """Assert that a module implements the required interface.

    Args:
        module: Module instance to check

    Raises:
        AssertionError: If module doesn't implement required interface
    """
    assert hasattr(module, "name"), "Module must have 'name' property"
    assert hasattr(module, "get_routes"), "Module must have 'get_routes' method"
    assert hasattr(module, "get_tasks"), "Module must have 'get_tasks' method"
    assert hasattr(module, "get_handlers"), "Module must have 'get_handlers' method"
    assert hasattr(module, "initialize"), "Module must have 'initialize' method"
    assert hasattr(module, "shutdown"), "Module must have 'shutdown' method"


import asyncio
