"""Environment detection and management."""

import os
from enum import Enum
from typing import Dict, Optional

import boto3
import requests
from pydantic import BaseModel


class Environment(Enum):
    """Environment types."""

    LOCALSTACK = "localstack"
    DEVELOPMENT = "development"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"
    CI = "ci"


class EnvironmentDetector:
    """Detect and manage runtime environment."""

    @staticmethod
    def detect() -> Environment:
        """Detect current environment based on various signals.

        Returns:
            Detected environment
        """
        # Check for explicit LocalStack flag
        if os.getenv("LOCALSTACK", "").lower() in ("true", "1", "yes"):
            return Environment.LOCALSTACK

        # Check for CI environment
        if os.getenv("CI", "").lower() in ("true", "1", "yes"):
            return Environment.CI

        # Check for explicit environment variable
        env_value = os.getenv("ENVIRONMENT", "").lower()
        if env_value:
            try:
                return Environment(env_value)
            except ValueError:
                pass

        # Check if LocalStack is running
        if EnvironmentDetector._is_localstack_running():
            return Environment.LOCALSTACK

        # Default to development
        return Environment.DEVELOPMENT

    @staticmethod
    def _is_localstack_running() -> bool:
        """Check if LocalStack is running on localhost."""
        try:
            response = requests.get(
                "http://localhost:4566/_localstack/health", timeout=1
            )
            return response.status_code == 200
        except Exception:
            return False

    @staticmethod
    def is_local() -> bool:
        """Check if running in local development."""
        env = EnvironmentDetector.detect()
        return env in (Environment.LOCALSTACK, Environment.DEVELOPMENT)

    @staticmethod
    def is_cloud() -> bool:
        """Check if running in cloud environment."""
        env = EnvironmentDetector.detect()
        return env in (Environment.STAGING, Environment.PRODUCTION)

    @staticmethod
    def requires_auth() -> bool:
        """Check if environment requires authentication."""
        env = EnvironmentDetector.detect()
        return env in (Environment.STAGING, Environment.PRODUCTION)


class ServiceEndpoints(BaseModel):
    """Service endpoint configuration."""

    dynamodb: Optional[str] = None
    s3: Optional[str] = None
    sqs: Optional[str] = None
    lambda_: Optional[str] = None
    events: Optional[str] = None
    ssm: Optional[str] = None
    redis: str = "localhost"
    postgres: str = "localhost"


class EnvironmentManager:
    """Manage environment-specific configurations."""

    _endpoints_cache: Dict[Environment, ServiceEndpoints] = {}

    @classmethod
    def get_endpoints(
        cls, environment: Optional[Environment] = None
    ) -> ServiceEndpoints:
        """Get service endpoints for environment.

        Args:
            environment: Target environment (auto-detected if None)

        Returns:
            Service endpoints configuration
        """
        env = environment or EnvironmentDetector.detect()

        if env not in cls._endpoints_cache:
            cls._endpoints_cache[env] = cls._resolve_endpoints(env)

        return cls._endpoints_cache[env]

    @classmethod
    def _resolve_endpoints(cls, environment: Environment) -> ServiceEndpoints:
        """Resolve endpoints for environment.

        Args:
            environment: Target environment

        Returns:
            Resolved endpoints
        """
        if environment == Environment.LOCALSTACK:
            return ServiceEndpoints(
                dynamodb="http://localhost:4566",
                s3="http://localhost:4566",
                sqs="http://localhost:4566",
                lambda_="http://localhost:4566",
                events="http://localhost:4566",
                ssm="http://localhost:4566",
                redis="localhost:6379",
                postgres="localhost:5432",
            )
        elif environment == Environment.CI:
            return ServiceEndpoints(
                dynamodb="http://localstack:4566",
                s3="http://localstack:4566",
                sqs="http://localstack:4566",
                lambda_="http://localstack:4566",
                events="http://localstack:4566",
                ssm="http://localstack:4566",
                redis="redis:6379",
                postgres="postgres:5432",
            )
        elif environment in (Environment.STAGING, Environment.PRODUCTION):
            # Cloud endpoints - use AWS defaults
            return ServiceEndpoints(
                redis=os.getenv("REDIS_ENDPOINT", "redis-cluster.aws.com"),
                postgres=os.getenv("DB_ENDPOINT", "postgres.aws.com"),
            )
        else:
            # Development - check what's available
            endpoints = ServiceEndpoints()

            # Check if LocalStack is available
            if cls._check_service("http://localhost:4566/_localstack/health"):
                endpoints.dynamodb = "http://localhost:4566"
                endpoints.s3 = "http://localhost:4566"
                endpoints.sqs = "http://localhost:4566"
                endpoints.lambda_ = "http://localhost:4566"
                endpoints.events = "http://localhost:4566"
                endpoints.ssm = "http://localhost:4566"

            # Check Redis
            if cls._check_redis("localhost", 6379):
                endpoints.redis = "localhost:6379"

            # Check Postgres
            if cls._check_postgres("localhost", 5432):
                endpoints.postgres = "localhost:5432"

            return endpoints

    @staticmethod
    def _check_service(url: str) -> bool:
        """Check if service is available."""
        try:
            response = requests.get(url, timeout=1)
            return response.status_code == 200
        except Exception:
            return False

    @staticmethod
    def _check_redis(host: str, port: int) -> bool:
        """Check if Redis is available."""
        try:
            import redis

            client = redis.Redis(host=host, port=port, socket_connect_timeout=1)
            client.ping()
            return True
        except Exception:
            return False

    @staticmethod
    def _check_postgres(host: str, port: int) -> bool:
        """Check if Postgres is available."""
        try:
            import psycopg2

            conn = psycopg2.connect(
                host=host,
                port=port,
                database="postgres",
                user="postgres",
                password="postgres",
                connect_timeout=1,
            )
            conn.close()
            return True
        except Exception:
            return False

    @classmethod
    def get_aws_client(cls, service: str, **kwargs):
        """Get AWS client with appropriate endpoint.

        Args:
            service: AWS service name
            **kwargs: Additional boto3 client arguments

        Returns:
            Configured boto3 client
        """
        env = EnvironmentDetector.detect()
        endpoints = cls.get_endpoints(env)

        # Get endpoint for service
        endpoint_url = getattr(endpoints, service, None)

        if endpoint_url:
            kwargs["endpoint_url"] = endpoint_url
            # Use dummy credentials for LocalStack
            if env == Environment.LOCALSTACK:
                kwargs["aws_access_key_id"] = "test"
                kwargs["aws_secret_access_key"] = "test"
                kwargs["region_name"] = kwargs.get("region_name", "us-east-1")

        return boto3.client(service, **kwargs)

    @classmethod
    def get_aws_resource(cls, service: str, **kwargs):
        """Get AWS resource with appropriate endpoint.

        Args:
            service: AWS service name
            **kwargs: Additional boto3 resource arguments

        Returns:
            Configured boto3 resource
        """
        env = EnvironmentDetector.detect()
        endpoints = cls.get_endpoints(env)

        # Get endpoint for service
        endpoint_url = getattr(endpoints, service, None)

        if endpoint_url:
            kwargs["endpoint_url"] = endpoint_url
            # Use dummy credentials for LocalStack
            if env == Environment.LOCALSTACK:
                kwargs["aws_access_key_id"] = "test"
                kwargs["aws_secret_access_key"] = "test"
                kwargs["region_name"] = kwargs.get("region_name", "us-east-1")

        return boto3.resource(service, **kwargs)
