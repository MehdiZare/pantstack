"""Pytest configuration and fixtures for auth service tests."""

import os
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from dependency_injector import containers, providers
from fastapi.testclient import TestClient


# Mock container for testing
class TestContainer(containers.DeclarativeContainer):
    """Test container with mocked dependencies."""

    # Mock Supabase client
    supabase_client = providers.Singleton(lambda: MagicMock())

    # Mock Redis client
    redis_client = providers.Singleton(lambda: MagicMock())

    # Mock config
    config = providers.Singleton(
        lambda: MagicMock(
            JWT_SECRET="test-secret",
            JWT_ALGORITHM="HS256",
            JWT_EXPIRY_MINUTES=15,
            SUPABASE_URL="http://test.supabase.co",
            SUPABASE_ANON_KEY="test-key",
            REDIS_HOST="localhost",
            REDIS_PORT=6379,
        )
    )


@pytest.fixture
def test_container() -> TestContainer:
    """Provide test container with mocked dependencies."""
    container = TestContainer()
    container.wire(
        modules=["services.auth.lib.services", "services.auth.lib.repositories"]
    )
    return container


@pytest.fixture
def mock_dynamodb():
    """Mock DynamoDB tables."""
    with patch("boto3.resource") as mock_resource:
        mock_table = MagicMock()
        mock_resource.return_value.Table.return_value = mock_table
        yield mock_table


@pytest.fixture
def mock_sqs():
    """Mock SQS client."""
    with patch("boto3.client") as mock_client:
        mock_sqs = MagicMock()
        mock_client.return_value = mock_sqs
        yield mock_sqs


@pytest.fixture
def mock_eventbridge():
    """Mock EventBridge client."""
    with patch("boto3.client") as mock_client:
        mock_events = MagicMock()
        mock_client.return_value = mock_events
        yield mock_events


@pytest.fixture
def api_client() -> Generator[TestClient, None, None]:
    """Create test client for FastAPI application."""
    # Import here to avoid circular imports
    from fastapi import FastAPI

    from services.auth.src.api.routes import router

    app = FastAPI()
    app.include_router(router)

    with TestClient(app) as client:
        yield client


@pytest.fixture
def auth_headers():
    """Provide authorization headers for testing."""
    return {"Authorization": "Bearer test-token-123"}


@pytest.fixture
def sample_user():
    """Provide sample user data."""
    return {
        "id": "user-123",
        "email": "test@example.com",
        "name": "Test User",
        "role": "user",
        "is_active": True,
    }


@pytest.fixture
def sample_jwt_payload():
    """Provide sample JWT payload."""
    return {
        "sub": "user-123",
        "email": "test@example.com",
        "role": "user",
        "exp": 9999999999,  # Far future
    }


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables for each test."""
    original_env = os.environ.copy()

    # Set test environment variables
    os.environ["ENVIRONMENT"] = "test"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)
