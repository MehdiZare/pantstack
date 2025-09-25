"""Configuration mixin and base configuration classes."""

import os
from functools import cached_property
from pathlib import Path
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

T = TypeVar("T", bound=BaseSettings)


class ConfigMixin(Generic[T]):
    """Mixin to inject configuration into any class.

    This mixin provides a standardized way to inject and access configuration
    in any class throughout the application.
    """

    _config_class: Type[T]
    _config_instance: Optional[T] = None

    @property
    def config(self) -> T:
        """Lazy-load configuration instance.

        Returns:
            Configuration instance of type T
        """
        if self._config_instance is None:
            self._config_instance = self._load_config()
        return self._config_instance

    def _load_config(self) -> T:
        """Load configuration. Override for custom loading logic.

        Returns:
            Configuration instance
        """
        if not hasattr(self, "_config_class"):
            raise AttributeError(
                f"{self.__class__.__name__} must define _config_class attribute"
            )
        return self._config_class()

    def inject_config(self, config: T) -> None:
        """Explicitly inject configuration.

        Args:
            config: Configuration instance to inject
        """
        self._config_instance = config

    def reload_config(self) -> None:
        """Reload configuration from source."""
        self._config_instance = None


class BaseConfig(BaseSettings):
    """Base configuration with common settings."""

    # Application settings
    app_name: str = Field(default="pantstack", description="Application name")
    environment: str = Field(default="development", description="Environment name")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    service_name: str = Field(default="", description="Current service name")

    # API settings
    api_version: str = Field(default="v1", description="API version")
    api_prefix: str = Field(default="/api", description="API prefix")
    cors_origins: List[str] = Field(default=["*"], description="CORS origins")
    rate_limit: int = Field(default=100, description="Rate limit per minute")

    # Security
    secret_key: str = Field(
        default="change-me-in-production", description="Secret key for JWT"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiration_hours: int = Field(default=24, description="JWT expiration in hours")
    internal_api_key: str = Field(
        default="", description="API key for internal service communication"
    )

    model_config = SettingsConfigDict(
        env_file=None,  # Don't auto-load .env - we'll handle it explicitly
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",
        env_nested_delimiter="__",  # Allow nested fields with __
    )

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        """Validate environment value."""
        allowed = ["development", "testing", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v = v.upper()
        if v not in allowed:
            raise ValueError(f"Log level must be one of {allowed}")
        return v

    @classmethod
    def from_yaml(cls, path: str) -> "BaseConfig":
        """Load configuration from YAML file.

        Args:
            path: Path to YAML file

        Returns:
            Configuration instance
        """
        yaml_path = Path(path)
        if not yaml_path.exists():
            print(f"⚠️ Config file not found: {path}, using defaults")
            return cls()

        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f) or {}

        # Merge with defaults if defaults.yaml exists
        defaults_path = Path("config/defaults.yaml")
        if defaults_path.exists():
            with open(defaults_path, "r") as f:
                defaults = yaml.safe_load(f) or {}
            # Deep merge defaults with loaded data
            for key, value in defaults.items():
                if key not in data:
                    data[key] = value

        # Create instance without loading .env file to avoid conflicts
        # Use model_validate instead of direct instantiation to avoid env loading
        return cls.model_validate(data)

    @classmethod
    def from_environment(cls) -> "BaseConfig":
        """Load configuration based on environment.

        Returns:
            Configuration instance with environment-specific settings
        """
        env = os.getenv("ENVIRONMENT", "development")

        # Try to load from environment-specific file
        config_paths = [
            f"config/environments/{env}.yaml",
            f"config/{env}.yaml",
            "config/settings.yaml",
        ]

        for path in config_paths:
            if Path(path).exists():
                config = cls.from_yaml(path)
                config.environment = env
                return config

        # Fall back to environment variables only
        config = cls()
        config.environment = env
        return config

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary.

        Returns:
            Configuration as dictionary
        """
        return self.model_dump()

    def mask_secrets(self) -> Dict[str, Any]:
        """Get configuration with masked secrets.

        Returns:
            Configuration dictionary with secrets masked
        """
        data = self.to_dict()
        secret_keys = ["secret_key", "password", "token", "api_key", "private_key"]

        def mask_value(key: str, value: Any) -> Any:
            if any(secret in key.lower() for secret in secret_keys):
                if isinstance(value, str) and value:
                    return value[:4] + "****" if len(value) > 4 else "****"
            return value

        def mask_dict(d: dict) -> dict:
            return {
                k: mask_value(k, v) if not isinstance(v, dict) else mask_dict(v)
                for k, v in d.items()
            }

        return mask_dict(data)


class DatabaseConfig(BaseSettings):
    """Database configuration."""

    # Supabase settings
    supabase_url: str = Field(default="", description="Supabase URL")
    supabase_anon_key: str = Field(default="", description="Supabase anonymous key")
    supabase_service_key: str = Field(default="", description="Supabase service key")

    # Connection pooling
    pool_size: int = Field(default=10, description="Connection pool size")
    max_overflow: int = Field(default=20, description="Max overflow connections")
    pool_timeout: int = Field(default=30, description="Pool timeout in seconds")
    pool_recycle: int = Field(default=3600, description="Pool recycle time in seconds")

    # Query settings
    statement_timeout: int = Field(default=30000, description="Statement timeout in ms")
    lock_timeout: int = Field(default=10000, description="Lock timeout in ms")

    model_config = SettingsConfigDict(env_prefix="DB_")

    @property
    def is_configured(self) -> bool:
        """Check if database is configured."""
        return bool(self.supabase_url and self.supabase_anon_key)


class RedisConfig(BaseSettings):
    """Redis configuration."""

    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, description="Redis port")
    db: int = Field(default=0, description="Redis database number")
    password: Optional[str] = Field(default=None, description="Redis password")
    ssl: bool = Field(default=False, description="Use SSL connection")
    socket_timeout: int = Field(default=5, description="Socket timeout in seconds")
    connection_pool_max_connections: int = Field(
        default=50, description="Max connections in pool"
    )

    model_config = SettingsConfigDict(env_prefix="REDIS_")

    @property
    def url(self) -> str:
        """Get Redis connection URL."""
        auth = f":{self.password}@" if self.password else ""
        protocol = "rediss" if self.ssl else "redis"
        return f"{protocol}://{auth}{self.host}:{self.port}/{self.db}"


class CeleryConfig(BaseSettings):
    """Celery configuration."""

    broker_url: str = Field(
        default="redis://localhost:6379/0", description="Broker URL"
    )
    result_backend: str = Field(
        default="redis://localhost:6379/0", description="Result backend"
    )
    task_serializer: str = Field(default="json", description="Task serializer")
    result_serializer: str = Field(default="json", description="Result serializer")
    accept_content: List[str] = Field(
        default=["json"], description="Accepted content types"
    )
    timezone: str = Field(default="UTC", description="Timezone")
    enable_utc: bool = Field(default=True, description="Enable UTC")
    task_track_started: bool = Field(default=True, description="Track started tasks")
    task_time_limit: int = Field(default=300, description="Task time limit in seconds")
    task_soft_time_limit: int = Field(default=240, description="Task soft time limit")
    worker_prefetch_multiplier: int = Field(
        default=4, description="Worker prefetch multiplier"
    )
    worker_max_tasks_per_child: int = Field(
        default=1000, description="Max tasks per child"
    )

    # Task routing
    task_routes: Dict[str, str] = Field(
        default_factory=dict, description="Task routing rules"
    )
    task_default_queue: str = Field(default="default", description="Default queue name")

    model_config = SettingsConfigDict(env_prefix="CELERY_")


class AWSConfig(BaseSettings):
    """AWS services configuration."""

    region: str = Field(default="us-east-1", description="AWS region")
    account_id: str = Field(default="", description="AWS account ID")

    # S3
    s3_bucket: str = Field(default="", description="S3 bucket name")
    s3_prefix: str = Field(default="", description="S3 key prefix")

    # SQS
    sqs_queue_url: Optional[str] = Field(default=None, description="SQS queue URL")
    sqs_dlq_url: Optional[str] = Field(default=None, description="SQS DLQ URL")

    # EventBridge
    eventbridge_bus: Optional[str] = Field(
        default=None, description="EventBridge bus name"
    )

    # Lambda
    lambda_role_arn: Optional[str] = Field(
        default=None, description="Lambda execution role ARN"
    )

    # LocalStack support
    localstack_enabled: bool = Field(default=False, description="Use LocalStack")
    localstack_endpoint: str = Field(
        default="http://localhost:4566", description="LocalStack endpoint"
    )

    model_config = SettingsConfigDict(env_prefix="AWS_")

    @property
    def endpoint_url(self) -> Optional[str]:
        """Get AWS endpoint URL (for LocalStack)."""
        return self.localstack_endpoint if self.localstack_enabled else None
