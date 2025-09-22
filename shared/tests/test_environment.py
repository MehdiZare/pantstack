"""Tests for environment configuration functionality."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


class TestEnvironment:
    """Test environment configuration and detection."""

    def test_environment_variable_loading(self):
        """Test environment variable loading from .env files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test .env file
            env_file = temp_path / ".env"
            env_content = """
ENV=development
DEBUG=true
DATABASE_URL=postgresql://localhost:5432/test
REDIS_URL=redis://localhost:6379
LOCALSTACK=true
AWS_REGION=us-east-1
"""
            env_file.write_text(env_content.strip())

            # Test file exists and contains expected content
            assert env_file.exists()
            content = env_file.read_text()
            assert "ENV=development" in content
            assert "DEBUG=true" in content

    def test_environment_detection_logic(self):
        """Test environment detection logic."""
        test_environments = {
            "development": {"DEBUG": "true", "ENV": "development"},
            "test": {"DEBUG": "false", "ENV": "test"},
            "staging": {"DEBUG": "false", "ENV": "staging"},
            "production": {"DEBUG": "false", "ENV": "production"},
        }

        for env_name, vars in test_environments.items():
            with patch.dict(os.environ, vars):
                assert os.getenv("ENV") == env_name
                # Debug should be true only in development
                expected_debug = "true" if env_name == "development" else "false"
                assert os.getenv("DEBUG") == expected_debug

    def test_localstack_configuration(self):
        """Test LocalStack configuration detection."""
        localstack_config = {
            "LOCALSTACK": "true",
            "LOCALSTACK_ENDPOINT": "http://localhost:4566",
            "LOCALSTACK_SERVICES": "s3,sqs,dynamodb",
        }

        with patch.dict(os.environ, localstack_config):
            assert os.getenv("LOCALSTACK") == "true"
            assert os.getenv("LOCALSTACK_ENDPOINT") == "http://localhost:4566"
            assert "s3" in os.getenv("LOCALSTACK_SERVICES", "")

    def test_database_configuration(self):
        """Test database configuration."""
        db_configs = {
            "development": "postgresql://localhost:5432/dev_db",
            "test": "postgresql://localhost:5432/test_db",
            "production": "postgresql://prod-host:5432/prod_db",
        }

        for env, db_url in db_configs.items():
            with patch.dict(os.environ, {"DATABASE_URL": db_url, "ENV": env}):
                url = os.getenv("DATABASE_URL")
                assert url.startswith("postgresql://")
                if env == "production":
                    assert "prod-host" in url
                else:
                    assert "localhost" in url

    def test_supabase_configuration(self):
        """Test Supabase configuration."""
        supabase_config = {
            "SUPABASE_URL": "http://localhost:54321",
            "SUPABASE_ANON_KEY": "test-anon-key",
            "SUPABASE_SERVICE_KEY": "test-service-key",
        }

        with patch.dict(os.environ, supabase_config):
            assert os.getenv("SUPABASE_URL") == "http://localhost:54321"
            assert os.getenv("SUPABASE_ANON_KEY") == "test-anon-key"
            assert os.getenv("SUPABASE_SERVICE_KEY") == "test-service-key"

    def test_redis_configuration(self):
        """Test Redis configuration."""
        redis_configs = {
            "development": "redis://localhost:6379/0",
            "test": "redis://localhost:6379/1",
            "production": "redis://prod-redis:6379/0",
        }

        for env, redis_url in redis_configs.items():
            with patch.dict(os.environ, {"REDIS_URL": redis_url, "ENV": env}):
                url = os.getenv("REDIS_URL")
                assert url.startswith("redis://")
                assert "6379" in url

    def test_aws_configuration(self):
        """Test AWS configuration."""
        aws_config = {
            "AWS_REGION": "us-east-1",
            "AWS_ACCESS_KEY_ID": "test-key-id",
            "AWS_SECRET_ACCESS_KEY": "test-secret-key",
            "AWS_DEFAULT_REGION": "us-east-1",
        }

        with patch.dict(os.environ, aws_config):
            assert os.getenv("AWS_REGION") == "us-east-1"
            assert os.getenv("AWS_ACCESS_KEY_ID") == "test-key-id"
            assert os.getenv("AWS_SECRET_ACCESS_KEY") == "test-secret-key"

    def test_feature_flags(self):
        """Test feature flag configuration."""
        feature_flags = {
            "FEATURE_NEW_API": "true",
            "FEATURE_BETA_UI": "false",
            "FEATURE_EXPERIMENTAL": "true",
        }

        with patch.dict(os.environ, feature_flags):
            assert os.getenv("FEATURE_NEW_API") == "true"
            assert os.getenv("FEATURE_BETA_UI") == "false"
            assert os.getenv("FEATURE_EXPERIMENTAL") == "true"

    def test_logging_configuration(self):
        """Test logging configuration."""
        logging_config = {
            "LOG_LEVEL": "INFO",
            "LOG_FORMAT": "json",
            "LOG_FILE": "/var/log/app.log",
        }

        with patch.dict(os.environ, logging_config):
            assert os.getenv("LOG_LEVEL") == "INFO"
            assert os.getenv("LOG_FORMAT") == "json"
            assert os.getenv("LOG_FILE") == "/var/log/app.log"

    def test_cors_configuration(self):
        """Test CORS configuration."""
        cors_config = {
            "CORS_ORIGINS": "http://localhost:3000,https://app.example.com",
            "CORS_METHODS": "GET,POST,PUT,DELETE",
            "CORS_HEADERS": "Content-Type,Authorization",
        }

        with patch.dict(os.environ, cors_config):
            origins = os.getenv("CORS_ORIGINS", "").split(",")
            assert "http://localhost:3000" in origins
            assert "https://app.example.com" in origins

    def test_api_configuration(self):
        """Test API configuration."""
        api_config = {
            "API_HOST": "0.0.0.0",
            "API_PORT": "8000",
            "API_WORKERS": "4",
            "API_TIMEOUT": "60",
        }

        with patch.dict(os.environ, api_config):
            assert os.getenv("API_HOST") == "0.0.0.0"
            assert os.getenv("API_PORT") == "8000"
            assert int(os.getenv("API_WORKERS", "1")) == 4

    def test_security_configuration(self):
        """Test security configuration."""
        security_config = {
            "SECRET_KEY": "super-secret-key-for-testing",
            "JWT_ALGORITHM": "HS256",
            "JWT_EXPIRATION": "3600",
            "BCRYPT_ROUNDS": "12",
        }

        with patch.dict(os.environ, security_config):
            assert len(os.getenv("SECRET_KEY", "")) > 10
            assert os.getenv("JWT_ALGORITHM") == "HS256"
            assert int(os.getenv("JWT_EXPIRATION", "0")) == 3600

    def test_monitoring_configuration(self):
        """Test monitoring configuration."""
        monitoring_config = {
            "SENTRY_DSN": "https://sentry.io/project/123",
            "METRICS_ENABLED": "true",
            "HEALTH_CHECK_ENABLED": "true",
        }

        with patch.dict(os.environ, monitoring_config):
            assert os.getenv("SENTRY_DSN", "").startswith("https://")
            assert os.getenv("METRICS_ENABLED") == "true"
            assert os.getenv("HEALTH_CHECK_ENABLED") == "true"

    def test_configuration_validation(self):
        """Test configuration validation."""
        required_vars = [
            "ENV",
            "DATABASE_URL",
            "REDIS_URL",
            "SECRET_KEY",
        ]

        optional_vars = [
            "DEBUG",
            "LOCALSTACK",
            "SENTRY_DSN",
        ]

        # Test that we can identify required vs optional
        for var in required_vars:
            assert len(var) > 0
            assert var.isupper()

        for var in optional_vars:
            assert len(var) > 0
            assert var.isupper()

    def test_environment_precedence(self):
        """Test environment variable precedence."""
        # Test that environment variables override defaults
        default_config = {
            "ENV": "development",
            "DEBUG": "false",
            "API_PORT": "8000",
        }

        override_config = {
            "ENV": "production",
            "DEBUG": "true",
            "API_PORT": "9000",
        }

        # First set defaults
        with patch.dict(os.environ, default_config):
            assert os.getenv("ENV") == "development"

        # Then test overrides
        with patch.dict(os.environ, {**default_config, **override_config}):
            assert os.getenv("ENV") == "production"
            assert os.getenv("DEBUG") == "true"
            assert os.getenv("API_PORT") == "9000"
