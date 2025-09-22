"""Core shared components for service architecture."""

from .config import BaseConfig, ConfigMixin
from .discovery import AutoDiscovery
from .registry import RouteDefinition, SecurityGroup, ServiceManifest, ServiceRegistry

__all__ = [
    "ServiceRegistry",
    "ServiceManifest",
    "RouteDefinition",
    "SecurityGroup",
    "AutoDiscovery",
    "ConfigMixin",
    "BaseConfig",
]
