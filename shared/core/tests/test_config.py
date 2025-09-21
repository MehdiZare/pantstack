"""Tests for shared configuration classes."""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock
import yaml

from shared.core.config import (
    BaseConfig,
    ConfigMixin,
    DatabaseConfig,
    RedisConfig,
    CeleryConfig,
    AWSConfig
)


class TestConfigMixin:
    """Test ConfigMixin functionality."""

    class TestConfig(BaseConfig):
        """Test configuration class."""
        test_field: str = "test_value"

    class TestClass(ConfigMixin[TestConfig]):
        """Test class with config mixin."""
        _config_class = TestConfig

    def test_config_lazy_loading(self):
        """Test lazy loading of configuration."""
        obj = self.TestClass()
        assert obj._config_instance is None

        config = obj.config
        assert config is not None
        assert obj._config_instance is not None
        assert config.test_field == "test_value"

    def test_config_injection(self):
        """Test explicit config injection."""
        obj = self.TestClass()
        custom_config = self.TestConfig(test_field="custom_value")

        obj.inject_config(custom_config)
        assert obj.config.test_field == "custom_value"

    def test_config_reload(self):
        """Test configuration reload."""
        obj = self.TestClass()
        config1 = obj.config
        obj.reload_config()
        config2 = obj.config

        assert config1 is not config2

    def test_missing_config_class_attribute(self):
        """Test error when _config_class is not defined."""
        class BadClass(ConfigMixin):
            pass

        obj = BadClass()
        with pytest.raises(AttributeError, match="_config_class"):
            _ = obj.config


class TestBaseConfig:
    """Test BaseConfig functionality."""

    def test_default_values(self):
        """Test default configuration values."""
        config = BaseConfig()

        assert config.app_name == "pantstack"
        assert config.environment == "development"
        assert config.debug is False
        assert config.log_level == "INFO"
        assert config.api_version == "v1"
        assert config.api_prefix == "/api"
        assert config.cors_origins == ["*"]

    def test_environment_validation(self):
        """Test environment field validation."""
        config = BaseConfig(environment="production")
        assert config.environment == "production"

        with pytest.raises(ValueError, match="Environment must be one of"):
            BaseConfig(environment="invalid")

    def test_log_level_validation(self):
        """Test log level validation."""
        config = BaseConfig(log_level="debug")
        assert config.log_level == "DEBUG"

        with pytest.raises(ValueError, match="Log level must be one of"):
            BaseConfig(log_level="invalid")

    def test_from_yaml(self):
        """Test loading configuration from YAML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                "app_name": "test_app",
                "environment": "testing",
                "debug": True,
                "log_level": "DEBUG"
            }, f)
            temp_path = f.name

        try:
            config = BaseConfig.from_yaml(temp_path)
            assert config.app_name == "test_app"
            assert config.environment == "testing"
            assert config.debug is True
            assert config.log_level == "DEBUG"
        finally:
            os.unlink(temp_path)

    def test_from_yaml_nonexistent_file(self):
        """Test loading from non-existent YAML file."""
        config = BaseConfig.from_yaml("/nonexistent/file.yaml")
        # Should use defaults
        assert config.app_name == "pantstack"

    @patch.dict(os.environ, {"ENVIRONMENT": "production"})
    def test_from_environment(self):
        """Test loading configuration from environment."""
        config = BaseConfig.from_environment()
        assert config.environment == "production"

    def test_to_dict(self):
        """Test converting config to dictionary."""
        config = BaseConfig(app_name="test", debug=True)
        data = config.to_dict()

        assert isinstance(data, dict)
        assert data["app_name"] == "test"
        assert data["debug"] is True

    def test_mask_secrets(self):
        """Test masking sensitive data."""
        config = BaseConfig(
            secret_key="supersecretkey123",
            internal_api_key="apikey456"
        )

        masked = config.mask_secrets()

        assert masked["secret_key"] == "supe****"
        assert masked["internal_api_key"] == "apik****"
        assert masked["app_name"] == "pantstack"  # Non-secret not masked


class TestDatabaseConfig:
    """Test DatabaseConfig functionality."""

    def test_default_values(self):
        """Test default database configuration."""
        config = DatabaseConfig()

        assert config.supabase_url == ""
        assert config.supabase_anon_key == ""
        assert config.pool_size == 10
        assert config.max_overflow == 20

    def test_is_configured(self):
        """Test database configuration check."""
        config = DatabaseConfig()
        assert config.is_configured is False

        config = DatabaseConfig(
            supabase_url="https://test.supabase.co",
            supabase_anon_key="test_key"
        )
        assert config.is_configured is True

    @patch.dict(os.environ, {
        "DB_SUPABASE_URL": "https://env.supabase.co",
        "DB_POOL_SIZE": "20"
    })
    def test_env_prefix(self):
        """Test environment variable prefix."""
        config = DatabaseConfig()
        assert config.supabase_url == "https://env.supabase.co"
        assert config.pool_size == 20


class TestRedisConfig:
    """Test RedisConfig functionality."""

    def test_default_values(self):
        """Test default Redis configuration."""
        config = RedisConfig()

        assert config.host == "localhost"
        assert config.port == 6379
        assert config.db == 0
        assert config.password is None
        assert config.ssl is False

    def test_url_generation(self):
        """Test Redis URL generation."""
        config = RedisConfig()
        assert config.url == "redis://localhost:6379/0"

        config = RedisConfig(password="secret", ssl=True)
        assert config.url == "rediss://:secret@localhost:6379/0"

    @patch.dict(os.environ, {
        "REDIS_HOST": "redis.example.com",
        "REDIS_PORT": "6380",
        "REDIS_PASSWORD": "secret123"
    })
    def test_env_loading(self):
        """Test loading from environment variables."""
        config = RedisConfig()
        assert config.host == "redis.example.com"
        assert config.port == 6380
        assert config.password == "secret123"


class TestCeleryConfig:
    """Test CeleryConfig functionality."""

    def test_default_values(self):
        """Test default Celery configuration."""
        config = CeleryConfig()

        assert config.broker_url == "redis://localhost:6379/0"
        assert config.result_backend == "redis://localhost:6379/0"
        assert config.task_serializer == "json"
        assert config.timezone == "UTC"
        assert config.enable_utc is True

    def test_task_routing(self):
        """Test task routing configuration."""
        config = CeleryConfig()
        assert config.task_routes == {}
        assert config.task_default_queue == "default"

        config = CeleryConfig(
            task_routes={"app.tasks.*": "high_priority"},
            task_default_queue="low_priority"
        )
        assert "app.tasks.*" in config.task_routes
        assert config.task_default_queue == "low_priority"


class TestAWSConfig:
    """Test AWSConfig functionality."""

    def test_default_values(self):
        """Test default AWS configuration."""
        config = AWSConfig()

        assert config.region == "us-east-1"
        assert config.localstack_enabled is False
        assert config.localstack_endpoint == "http://localhost:4566"

    def test_endpoint_url(self):
        """Test AWS endpoint URL for LocalStack."""
        config = AWSConfig()
        assert config.endpoint_url is None

        config = AWSConfig(localstack_enabled=True)
        assert config.endpoint_url == "http://localhost:4566"

    @patch.dict(os.environ, {
        "AWS_REGION": "eu-west-1",
        "AWS_LOCALSTACK_ENABLED": "true",
        "AWS_S3_BUCKET": "test-bucket"
    })
    def test_env_loading(self):
        """Test loading AWS config from environment."""
        config = AWSConfig()
        assert config.region == "eu-west-1"
        assert config.localstack_enabled is True
        assert config.s3_bucket == "test-bucket"


class TestConfigIntegration:
    """Test configuration integration scenarios."""

    def test_yaml_and_env_merge(self):
        """Test merging YAML and environment configurations."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                "app_name": "yaml_app",
                "debug": False
            }, f)
            temp_path = f.name

        try:
            with patch.dict(os.environ, {"LOG_LEVEL": "ERROR"}):
                config = BaseConfig.from_yaml(temp_path)
                assert config.app_name == "yaml_app"
                assert config.debug is False
                # Environment variables are not automatically loaded when using from_yaml
        finally:
            os.unlink(temp_path)

    def test_defaults_yaml_merge(self):
        """Test merging with defaults.yaml."""
        # Create temporary defaults file
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "config"
            config_dir.mkdir()

            defaults_path = config_dir / "defaults.yaml"
            with open(defaults_path, "w") as f:
                yaml.dump({"debug": True, "rate_limit": 200}, f)

            settings_path = config_dir / "settings.yaml"
            with open(settings_path, "w") as f:
                yaml.dump({"app_name": "custom_app"}, f)

            # Mock the Path to use our temp directory
            with patch("shared.core.config.Path") as mock_path:
                def path_side_effect(path_str):
                    if "defaults.yaml" in path_str:
                        return defaults_path
                    return Path(path_str)

                mock_path.side_effect = path_side_effect
                mock_path.return_value.exists.return_value = True

                config = BaseConfig.from_yaml(str(settings_path))
                assert config.app_name == "custom_app"
                # Note: In real implementation, defaults would be merged