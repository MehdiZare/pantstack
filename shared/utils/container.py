"""Container utilities for dependency injection."""

from typing import Any, Optional

from shared.core.config import BaseConfig

# Global container instance (set by entry points)
_global_container: Optional[Any] = None
_global_config: Optional[BaseConfig] = None


def set_container(container: Any) -> None:
    """Set the global container instance.

    Args:
        container: Container instance
    """
    global _global_container
    _global_container = container


def get_container() -> Any:
    """Get the global container instance.

    Returns:
        Container instance

    Raises:
        RuntimeError: If container not set
    """
    if _global_container is None:
        raise RuntimeError(
            "Container not initialized. Call set_container() first."
        )
    return _global_container


def set_config(config: BaseConfig) -> None:
    """Set the global configuration instance.

    Args:
        config: Configuration instance
    """
    global _global_config
    _global_config = config


def get_config() -> BaseConfig:
    """Get the global configuration instance.

    Returns:
        Configuration instance

    Raises:
        RuntimeError: If config not set
    """
    if _global_config is None:
        # Try to get from container
        try:
            container = get_container()
            if hasattr(container, "config"):
                return container.config()
        except RuntimeError:
            pass

        raise RuntimeError(
            "Configuration not initialized. Call set_config() first."
        )
    return _global_config


def get_service_container() -> Any:
    """FastAPI dependency to get the service container.

    Returns:
        Container instance for dependency injection
    """
    return get_container()