"""Configuration loading strategy for services."""

import os
from typing import Any, Dict, Optional, Type, TypeVar

from pydantic_settings import BaseSettings

T = TypeVar("T", bound=BaseSettings)


class ConfigLoader:
    """Configuration loader with environment-based strategy."""

    def __init__(self, env_file: Optional[str] = None):
        """Initialize config loader.

        Args:
            env_file: Path to .env file, defaults to .env in current directory
        """
        self.env_file = env_file or ".env"
        self._config_cache: Dict[str, Any] = {}

    def load_config(self, config_class: Type[T], **kwargs) -> T:
        """Load configuration for a given config class.

        Args:
            config_class: Pydantic BaseSettings class to instantiate
            **kwargs: Additional keyword arguments to pass to config class

        Returns:
            Instantiated configuration object
        """
        class_name = config_class.__name__

        # Return cached config if available
        if class_name in self._config_cache:
            return self._config_cache[class_name]

        # Create config instance
        config = config_class(_env_file=self.env_file, **kwargs)

        # Cache the config
        self._config_cache[class_name] = config

        return config

    def get_env(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get environment variable value.

        Args:
            key: Environment variable key
            default: Default value if key not found

        Returns:
            Environment variable value or default
        """
        return os.getenv(key, default)

    def set_env(self, key: str, value: str) -> None:
        """Set environment variable value.

        Args:
            key: Environment variable key
            value: Environment variable value
        """
        os.environ[key] = value

    def clear_cache(self) -> None:
        """Clear configuration cache."""
        self._config_cache.clear()


# Global config loader instance
config_loader = ConfigLoader()