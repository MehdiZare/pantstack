"""Configuration loading strategies for different environments."""

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional, Type, TypeVar

import boto3
import yaml

from shared.core.config import (
    AWSConfig,
    BaseConfig,
    CeleryConfig,
    DatabaseConfig,
    RedisConfig,
)
from shared.core.environment import Environment, EnvironmentManager

T = TypeVar("T", bound=BaseConfig)


class ConfigStrategy(ABC):
    """Abstract configuration loading strategy."""

    @abstractmethod
    def load_config(self, config_class: Type[T], service_name: str) -> T:
        """Load configuration for service.

        Args:
            config_class: Configuration class
            service_name: Service name

        Returns:
            Configuration instance
        """
        pass

    def _merge_configs(
        self, base: Dict[str, Any], override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deep merge configuration dictionaries.

        Args:
            base: Base configuration
            override: Override configuration

        Returns:
            Merged configuration
        """
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value

        return result


class LocalStackStrategy(ConfigStrategy):
    """Configuration strategy for LocalStack environment."""

    def load_config(self, config_class: Type[T], service_name: str) -> T:
        """Load LocalStack-optimized configuration.

        Args:
            config_class: Configuration class
            service_name: Service name

        Returns:
            Configuration with LocalStack endpoints
        """
        # Start with base configuration
        config = config_class()

        # Override with LocalStack-specific settings
        config.environment = "localstack"
        config.debug = True
        config.service_name = service_name

        # Configure AWS for LocalStack
        if hasattr(config, "aws"):
            config.aws = AWSConfig(
                region="us-east-1",
                localstack_enabled=True,
                localstack_endpoint="http://localhost:4566",
                s3_bucket=f"{service_name}-local",
                sqs_queue_url="http://localhost:4566/000000000000/main-queue",
                eventbridge_bus="default",
            )

        # Configure Redis for local
        if hasattr(config, "redis"):
            config.redis = RedisConfig(
                host="localhost",
                port=6379,
                db=0,
            )

        # Configure Celery for local
        if hasattr(config, "celery"):
            config.celery = CeleryConfig(
                broker_url="redis://localhost:6379/0",
                result_backend="redis://localhost:6379/0",
                task_default_queue=service_name,
            )

        # Configure database for local
        if hasattr(config, "database"):
            config.database = DatabaseConfig(
                supabase_url=os.getenv("DB_SUPABASE_URL", "http://localhost:54321"),
                supabase_anon_key=os.getenv("DB_SUPABASE_ANON_KEY", "local-anon-key"),
            )

        return config


class DevelopmentStrategy(ConfigStrategy):
    """Configuration strategy for development environment."""

    def load_config(self, config_class: Type[T], service_name: str) -> T:
        """Load development configuration from files and environment.

        Args:
            config_class: Configuration class
            service_name: Service name

        Returns:
            Development configuration
        """
        # Check for config files
        config_paths = [
            f"config/services/{service_name}/development.yaml",
            "config/environments/development.yaml",
            "config/defaults.yaml",
        ]

        config_data = {}
        for path in config_paths:
            if Path(path).exists():
                with open(path) as f:
                    file_data = yaml.safe_load(f) or {}
                    config_data = self._merge_configs(config_data, file_data)

        # Create config from merged data
        config = config_class(**config_data)
        config.environment = "development"
        config.service_name = service_name
        config.debug = True

        # Auto-detect LocalStack if available
        endpoints = EnvironmentManager.get_endpoints(Environment.DEVELOPMENT)
        if endpoints.dynamodb:  # LocalStack is available
            if hasattr(config, "aws"):
                config.aws.localstack_enabled = True
                config.aws.localstack_endpoint = endpoints.dynamodb

        return config


class TestStrategy(ConfigStrategy):
    """Configuration strategy for test environment."""

    def load_config(self, config_class: Type[T], service_name: str) -> T:
        """Load test configuration.

        Args:
            config_class: Configuration class
            service_name: Service name

        Returns:
            Test configuration
        """
        config = config_class()
        config.environment = "test"
        config.service_name = service_name
        config.debug = True

        # Use LocalStack in CI
        if os.getenv("CI"):
            if hasattr(config, "aws"):
                config.aws = AWSConfig(
                    region="us-east-1",
                    localstack_enabled=True,
                    localstack_endpoint="http://localstack:4566",
                )
            if hasattr(config, "redis"):
                config.redis.host = "redis"
            if hasattr(config, "database"):
                config.database.supabase_url = "http://postgres:5432"

        return config


class ProductionStrategy(ConfigStrategy):
    """Configuration strategy for production environment."""

    def __init__(self):
        """Initialize production strategy."""
        self._ssm_client = None
        self._secrets_cache: Dict[str, str] = {}

    @property
    def ssm_client(self):
        """Get SSM client."""
        if not self._ssm_client:
            self._ssm_client = boto3.client("ssm")
        return self._ssm_client

    def load_config(self, config_class: Type[T], service_name: str) -> T:
        """Load production configuration from SSM and environment.

        Args:
            config_class: Configuration class
            service_name: Service name

        Returns:
            Production configuration
        """
        # Load base configuration
        config = config_class()
        config.environment = "production"
        config.service_name = service_name
        config.debug = False

        # Load secrets from SSM Parameter Store
        self._load_ssm_parameters(config, service_name)

        # Load from environment variables (overrides)
        config = config_class.parse_obj(os.environ)

        return config

    def _load_ssm_parameters(self, config: BaseConfig, service_name: str):
        """Load parameters from SSM.

        Args:
            config: Configuration object
            service_name: Service name
        """
        try:
            # Get parameters for service
            prefix = f"/{service_name}/prod/"
            response = self.ssm_client.get_parameters_by_path(
                Path=prefix,
                Recursive=True,
                WithDecryption=True,
            )

            for param in response.get("Parameters", []):
                # Extract parameter name without prefix
                param_name = param["Name"].replace(prefix, "").replace("-", "_")

                # Set value on config
                if hasattr(config, param_name):
                    setattr(config, param_name, param["Value"])

        except Exception as e:
            print(f"Warning: Failed to load SSM parameters: {e}")


class StagingStrategy(ProductionStrategy):
    """Configuration strategy for staging environment."""

    def load_config(self, config_class: Type[T], service_name: str) -> T:
        """Load staging configuration.

        Args:
            config_class: Configuration class
            service_name: Service name

        Returns:
            Staging configuration
        """
        config = super().load_config(config_class, service_name)
        config.environment = "staging"
        config.debug = True  # Enable debug in staging
        return config


class ConfigLoader:
    """Main configuration loader with strategy pattern."""

    _strategies = {
        Environment.LOCALSTACK: LocalStackStrategy(),
        Environment.DEVELOPMENT: DevelopmentStrategy(),
        Environment.TEST: TestStrategy(),
        Environment.STAGING: StagingStrategy(),
        Environment.PRODUCTION: ProductionStrategy(),
        Environment.CI: TestStrategy(),
    }

    @classmethod
    def load(
        cls,
        config_class: Type[T],
        service_name: str,
        environment: Optional[Environment] = None,
    ) -> T:
        """Load configuration for service.

        Args:
            config_class: Configuration class
            service_name: Service name
            environment: Target environment (auto-detected if None)

        Returns:
            Configuration instance
        """
        from shared.core.environment import EnvironmentDetector

        env = environment or EnvironmentDetector.detect()
        strategy = cls._strategies.get(env, DevelopmentStrategy())

        # Load configuration
        config = strategy.load_config(config_class, service_name)

        # Validate configuration
        cls._validate_config(config, env)

        return config

    @classmethod
    def _validate_config(cls, config: BaseConfig, environment: Environment):
        """Validate configuration for environment.

        Args:
            config: Configuration to validate
            environment: Target environment

        Raises:
            ValueError: If configuration is invalid
        """
        # Production requires certain fields
        if environment == Environment.PRODUCTION:
            if config.secret_key == "change-me-in-production":
                raise ValueError("Production requires a real secret key")
            if config.debug:
                raise ValueError("Debug must be disabled in production")

        # Validate AWS configuration if present
        if hasattr(config, "aws") and environment in (
            Environment.STAGING,
            Environment.PRODUCTION,
        ):
            if not config.aws.region:
                raise ValueError("AWS region is required")
            if not config.aws.account_id:
                raise ValueError("AWS account ID is required")
