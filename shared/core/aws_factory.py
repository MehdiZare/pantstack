"""AWS client factory with LocalStack support."""

from functools import lru_cache
from typing import Any, Dict, Optional

import boto3
from botocore.client import BaseClient
from botocore.config import Config

from shared.core.config import AWSConfig
from shared.core.environment import EnvironmentDetector, EnvironmentManager


class AWSClientFactory:
    """Factory for creating AWS clients with automatic LocalStack detection."""

    def __init__(self, config: Optional[AWSConfig] = None):
        """Initialize AWS client factory.

        Args:
            config: AWS configuration (auto-loaded if None)
        """
        self.config = config or self._load_default_config()
        self._clients: Dict[str, BaseClient] = {}

    def _load_default_config(self) -> AWSConfig:
        """Load default AWS configuration.

        Returns:
            AWS configuration
        """
        from shared.core.config import BaseConfig
        from shared.core.config_strategy import ConfigLoader

        base_config = ConfigLoader.load(BaseConfig, "shared")
        if hasattr(base_config, "aws"):
            return base_config.aws
        return AWSConfig()

    @lru_cache(maxsize=None)
    def get_client(
        self, service_name: str, region_name: Optional[str] = None, **kwargs
    ) -> BaseClient:
        """Get or create AWS client.

        Args:
            service_name: AWS service name (e.g., 'dynamodb', 's3')
            region_name: AWS region (uses config default if None)
            **kwargs: Additional boto3 client arguments

        Returns:
            Configured boto3 client
        """
        # Use cached client if available
        cache_key = f"{service_name}:{region_name}"
        if cache_key in self._clients:
            return self._clients[cache_key]

        # Create new client
        client = self._create_client(service_name, region_name, **kwargs)
        self._clients[cache_key] = client
        return client

    def _create_client(
        self, service_name: str, region_name: Optional[str] = None, **kwargs
    ) -> BaseClient:
        """Create new AWS client.

        Args:
            service_name: AWS service name
            region_name: AWS region
            **kwargs: Additional boto3 client arguments

        Returns:
            Configured boto3 client
        """
        # Determine endpoint URL
        endpoint_url = self._get_endpoint_url(service_name)

        # Set region
        if not region_name:
            region_name = self.config.region or "us-east-1"

        # Build client configuration
        client_config = Config(
            region_name=region_name,
            retries={"max_attempts": 3, "mode": "adaptive"},
        )

        # Build client arguments
        client_kwargs = {
            "service_name": service_name,
            "config": client_config,
            **kwargs,
        }

        # Add endpoint URL if using LocalStack
        if endpoint_url:
            client_kwargs["endpoint_url"] = endpoint_url

            # Use dummy credentials for LocalStack
            if self.config.localstack_enabled:
                client_kwargs["aws_access_key_id"] = "test"
                client_kwargs["aws_secret_access_key"] = "test"

        return boto3.client(**client_kwargs)

    def _get_endpoint_url(self, service_name: str) -> Optional[str]:
        """Get endpoint URL for service.

        Args:
            service_name: AWS service name

        Returns:
            Endpoint URL or None
        """
        # Check if LocalStack is enabled
        if self.config.localstack_enabled:
            return self.config.localstack_endpoint

        # Check environment manager
        endpoints = EnvironmentManager.get_endpoints()
        return getattr(endpoints, service_name, None)

    def get_resource(
        self, service_name: str, region_name: Optional[str] = None, **kwargs
    ) -> Any:
        """Get AWS resource.

        Args:
            service_name: AWS service name
            region_name: AWS region
            **kwargs: Additional boto3 resource arguments

        Returns:
            Configured boto3 resource
        """
        # Determine endpoint URL
        endpoint_url = self._get_endpoint_url(service_name)

        # Set region
        if not region_name:
            region_name = self.config.region or "us-east-1"

        # Build resource arguments
        resource_kwargs = {
            "service_name": service_name,
            "region_name": region_name,
            **kwargs,
        }

        # Add endpoint URL if using LocalStack
        if endpoint_url:
            resource_kwargs["endpoint_url"] = endpoint_url

            # Use dummy credentials for LocalStack
            if self.config.localstack_enabled:
                resource_kwargs["aws_access_key_id"] = "test"
                resource_kwargs["aws_secret_access_key"] = "test"

        return boto3.resource(**resource_kwargs)

    # Convenience methods for common services
    @property
    def dynamodb(self):
        """Get DynamoDB resource."""
        return self.get_resource("dynamodb")

    @property
    def s3(self):
        """Get S3 client."""
        return self.get_client("s3")

    @property
    def sqs(self):
        """Get SQS client."""
        return self.get_client("sqs")

    @property
    def events(self):
        """Get EventBridge client."""
        return self.get_client("events")

    @property
    def lambda_(self):
        """Get Lambda client."""
        return self.get_client("lambda")

    @property
    def ssm(self):
        """Get SSM client."""
        return self.get_client("ssm")

    @property
    def logs(self):
        """Get CloudWatch Logs client."""
        return self.get_client("logs")

    def clear_cache(self):
        """Clear client cache."""
        self._clients.clear()
        self.get_client.cache_clear()


# Global factory instance
_global_factory: Optional[AWSClientFactory] = None


def get_aws_factory(config: Optional[AWSConfig] = None) -> AWSClientFactory:
    """Get or create global AWS client factory.

    Args:
        config: AWS configuration (uses default if None)

    Returns:
        AWS client factory
    """
    global _global_factory
    if _global_factory is None or config:
        _global_factory = AWSClientFactory(config)
    return _global_factory


def get_aws_client(service_name: str, **kwargs) -> BaseClient:
    """Get AWS client using global factory.

    Args:
        service_name: AWS service name
        **kwargs: Additional client arguments

    Returns:
        Configured boto3 client
    """
    factory = get_aws_factory()
    return factory.get_client(service_name, **kwargs)


def get_aws_resource(service_name: str, **kwargs) -> Any:
    """Get AWS resource using global factory.

    Args:
        service_name: AWS service name
        **kwargs: Additional resource arguments

    Returns:
        Configured boto3 resource
    """
    factory = get_aws_factory()
    return factory.get_resource(service_name, **kwargs)
