"""Redis client for auth service."""

from typing import Optional

import redis
from redis.asyncio import Redis as AsyncRedis

from stack.libs.shared.core.config import RedisConfig


def get_redis_client(config: RedisConfig) -> redis.Redis:
    """Get Redis client instance.

    Args:
        config: Redis configuration

    Returns:
        Redis client
    """
    return redis.Redis(
        host=config.host,
        port=config.port,
        db=config.db,
        password=config.password,
        ssl=config.ssl,
        socket_timeout=config.socket_timeout,
        connection_pool_kwargs={
            "max_connections": config.connection_pool_max_connections
        },
        decode_responses=True,
    )


def get_async_redis_client(config: RedisConfig) -> AsyncRedis:
    """Get async Redis client instance.

    Args:
        config: Redis configuration

    Returns:
        Async Redis client
    """
    return AsyncRedis(
        host=config.host,
        port=config.port,
        db=config.db,
        password=config.password,
        ssl=config.ssl,
        socket_timeout=config.socket_timeout,
        max_connections=config.connection_pool_max_connections,
        decode_responses=True,
    )


class RedisClient:
    """Wrapper for Redis client with additional functionality."""

    def __init__(self, config: RedisConfig):
        """Initialize Redis client wrapper.

        Args:
            config: Redis configuration
        """
        self.config = config
        self._sync_client: Optional[redis.Redis] = None
        self._async_client: Optional[AsyncRedis] = None

    @property
    def sync(self) -> redis.Redis:
        """Get synchronous Redis client."""
        if not self._sync_client:
            self._sync_client = get_redis_client(self.config)
        return self._sync_client

    @property
    def async_client(self) -> AsyncRedis:
        """Get asynchronous Redis client."""
        if not self._async_client:
            self._async_client = get_async_redis_client(self.config)
        return self._async_client

    def close(self):
        """Close Redis connections."""
        if self._sync_client:
            self._sync_client.close()
        if self._async_client:
            self._async_client.close()