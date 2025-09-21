"""Core shared components for service architecture."""

from .registry import ServiceRegistry, ServiceManifest, RouteDefinition, SecurityGroup
from .discovery import AutoDiscovery
from .config import ConfigMixin, BaseConfig

__all__ = [
    "ServiceRegistry",
    "ServiceManifest",
    "RouteDefinition",
    "SecurityGroup",
    "AutoDiscovery",
    "ConfigMixin",
    "BaseConfig",
]