"""Service registry and discovery patterns."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Callable, Dict, List, Optional

from pydantic import BaseModel, Field


class SecurityGroup(Enum):
    """Route security groups for API endpoints."""

    PUBLIC = "public"  # No authentication required
    AUTHENTICATED = "authenticated"  # Valid user session required
    ADMIN = "admin"  # Admin role required
    INTERNAL = "internal"  # Service-to-service only (API key)


class RouteDefinition(BaseModel):
    """API route metadata for registration."""

    path: str
    method: str
    handler: Callable
    security_group: SecurityGroup
    tags: List[str] = Field(default_factory=list)
    description: str = ""
    dependencies: List[Callable] = Field(default_factory=list)


class TaskDefinition(BaseModel):
    """Celery task metadata for registration."""

    name: str
    task_func: Callable
    queue: str = "default"
    priority: int = 5
    rate_limit: Optional[str] = None
    time_limit: Optional[int] = None


class HandlerDefinition(BaseModel):
    """Event handler metadata for Lambda/event processing."""

    event_type: str
    handler_func: Callable
    source: str = ""  # e.g., "sqs", "eventbridge", "direct"
    batch_size: int = 1


class ServiceManifest(BaseModel):
    """Service registration manifest."""

    service_name: str
    version: str
    description: str = ""

    # API routes
    routes: List[RouteDefinition] = Field(default_factory=list)

    # Celery tasks
    tasks: List[TaskDefinition] = Field(default_factory=list)
    task_modules: List[str] = Field(default_factory=list)  # Module names to import

    # Event handlers
    handlers: List[HandlerDefinition] = Field(default_factory=list)

    # Service metadata
    dependencies: List[str] = Field(default_factory=list)  # Other services this depends on
    health_check_path: str = "/health"
    metrics_enabled: bool = True


class ServiceRegistry(ABC):
    """Base registry for service discovery and registration."""

    def __init__(self):
        self._manifests: Dict[str, ServiceManifest] = {}
        self._initialized = False

    @abstractmethod
    def discover_services(self) -> List[ServiceManifest]:
        """Discover all available services and their components."""
        pass

    def register(self, manifest: ServiceManifest) -> None:
        """Register a service manifest."""
        if manifest.service_name in self._manifests:
            print(f"⚠️ Service {manifest.service_name} already registered, overwriting...")

        self._manifests[manifest.service_name] = manifest
        print(f"✅ Registered service: {manifest.service_name} v{manifest.version}")

    def unregister(self, service_name: str) -> None:
        """Unregister a service."""
        if service_name in self._manifests:
            del self._manifests[service_name]
            print(f"🗑️ Unregistered service: {service_name}")

    def get_manifest(self, service_name: str) -> Optional[ServiceManifest]:
        """Get a specific service manifest."""
        return self._manifests.get(service_name)

    def get_all_manifests(self) -> List[ServiceManifest]:
        """Get all registered service manifests."""
        return list(self._manifests.values())

    def get_service_names(self) -> List[str]:
        """Get all registered service names."""
        return list(self._manifests.keys())

    def initialize(self) -> None:
        """Initialize registry by discovering services."""
        if not self._initialized:
            self.discover_services()
            self._initialized = True
            print(f"📦 Registry initialized with {len(self._manifests)} services")

    def get_dependencies_graph(self) -> Dict[str, List[str]]:
        """Get service dependency graph."""
        graph = {}
        for manifest in self._manifests.values():
            graph[manifest.service_name] = manifest.dependencies
        return graph

    def validate_dependencies(self) -> List[str]:
        """Validate that all service dependencies are met."""
        errors = []
        registered = set(self._manifests.keys())

        for manifest in self._manifests.values():
            for dep in manifest.dependencies:
                if dep not in registered:
                    errors.append(f"{manifest.service_name} depends on unregistered service: {dep}")

        return errors