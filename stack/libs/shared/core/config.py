"""Shared configuration classes for all services."""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class BaseConfig(BaseSettings):
    """Base configuration for all services."""

    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    service_name: str = Field(default="unnamed", env="SERVICE_NAME")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # JWT settings
    jwt_secret_key: str = Field(default="change-me-in-production", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_minutes: int = Field(default=60, env="JWT_EXPIRATION_MINUTES")

    class Config:
        env_file = ".env"
        case_sensitive = False


class DatabaseConfig(BaseSettings):
    """Database configuration."""

    # Supabase configuration
    supabase_url: str = Field(default="", env="SUPABASE_URL")
    supabase_key: str = Field(default="", env="SUPABASE_KEY")
    supabase_service_key: Optional[str] = Field(
        default=None, env="SUPABASE_SERVICE_KEY"
    )

    # Connection pool settings
    pool_size: int = Field(default=10, env="DB_POOL_SIZE")
    max_overflow: int = Field(default=20, env="DB_MAX_OVERFLOW")
    pool_timeout: int = Field(default=30, env="DB_POOL_TIMEOUT")

    class Config:
        env_file = ".env"


class RedisConfig(BaseSettings):
    """Redis configuration."""

    host: str = Field(default="localhost", env="REDIS_HOST")
    port: int = Field(default=6379, env="REDIS_PORT")
    password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    db: int = Field(default=0, env="REDIS_DB")

    # Connection pool settings
    max_connections: int = Field(default=50, env="REDIS_MAX_CONNECTIONS")
    decode_responses: bool = Field(default=True, env="REDIS_DECODE_RESPONSES")

    @property
    def url(self) -> str:
        """Get Redis connection URL."""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"

    class Config:
        env_file = ".env"


class AWSConfig(BaseSettings):
    """AWS configuration."""

    region: str = Field(default="us-east-1", env="AWS_REGION")
    access_key_id: Optional[str] = Field(default=None, env="AWS_ACCESS_KEY_ID")
    secret_access_key: Optional[str] = Field(default=None, env="AWS_SECRET_ACCESS_KEY")
    session_token: Optional[str] = Field(default=None, env="AWS_SESSION_TOKEN")

    # LocalStack settings
    localstack_endpoint: Optional[str] = Field(default=None, env="LOCALSTACK_ENDPOINT")
    use_localstack: bool = Field(default=False, env="USE_LOCALSTACK")

    # S3 settings
    s3_bucket_prefix: str = Field(default="pantstack", env="S3_BUCKET_PREFIX")

    # DynamoDB settings
    dynamodb_table_prefix: str = Field(default="pantstack", env="DYNAMODB_TABLE_PREFIX")

    @property
    def endpoint_url(self) -> Optional[str]:
        """Get AWS endpoint URL (for LocalStack)."""
        if self.use_localstack and self.localstack_endpoint:
            return self.localstack_endpoint
        return None

    class Config:
        env_file = ".env"


class CeleryConfig(BaseSettings):
    """Celery configuration."""

    broker_url: str = Field(default="redis://localhost:6379/0", env="CELERY_BROKER_URL")
    result_backend: str = Field(
        default="redis://localhost:6379/0", env="CELERY_RESULT_BACKEND"
    )

    # Task settings
    task_serializer: str = Field(default="json", env="CELERY_TASK_SERIALIZER")
    result_serializer: str = Field(default="json", env="CELERY_RESULT_SERIALIZER")
    accept_content: list = Field(default=["json"], env="CELERY_ACCEPT_CONTENT")
    timezone: str = Field(default="UTC", env="CELERY_TIMEZONE")
    enable_utc: bool = Field(default=True, env="CELERY_ENABLE_UTC")

    # Worker settings
    worker_prefetch_multiplier: int = Field(
        default=1, env="CELERY_WORKER_PREFETCH_MULTIPLIER"
    )
    worker_max_tasks_per_child: int = Field(
        default=1000, env="CELERY_WORKER_MAX_TASKS_PER_CHILD"
    )

    class Config:
        env_file = ".env"
