"""Shared dependency injection container infrastructure."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type

from dependency_injector import containers, providers


class BaseContainer(containers.DeclarativeContainer):
    """Base container for all services."""

    # Configuration provider - to be overridden by services
    config = providers.Configuration()


class InfrastructureContainer(containers.DeclarativeContainer):
    """Common infrastructure providers."""

    config = providers.DependenciesContainer()

    # Database providers
    database_url = providers.Callable(
        lambda config: config.database.url,
        config.provided,
    )

    # Redis providers
    redis_url = providers.Callable(
        lambda config: f"redis://{config.redis.host}:{config.redis.port}/{config.redis.db}",
        config.provided,
    )

    # AWS providers
    aws_config = providers.Dict(
        {
            "region_name": config.provided.aws.region,
            "endpoint_url": config.provided.aws.endpoint_url,
        }
    )


class RepositoryContainer(containers.DeclarativeContainer):
    """Base container for repository layer."""

    infrastructure = providers.DependenciesContainer()
    config = providers.DependenciesContainer()


class ServiceContainer(containers.DeclarativeContainer):
    """Base container for service layer."""

    repositories = providers.DependenciesContainer()
    infrastructure = providers.DependenciesContainer()
    config = providers.DependenciesContainer()


class ModuleRegistry:
    """Registry for service modules."""

    def __init__(self):
        self._modules: Dict[str, Any] = {}
        self._providers: Dict[str, providers.Provider] = {}

    def register_module(self, name: str, module: Any) -> None:
        """Register a module.

        Args:
            name: Module name
            module: Module instance
        """
        self._modules[name] = module

    def register_provider(self, name: str, provider: providers.Provider) -> None:
        """Register a provider.

        Args:
            name: Provider name
            provider: Provider instance
        """
        self._providers[name] = provider

    def get_module(self, name: str) -> Optional[Any]:
        """Get a registered module.

        Args:
            name: Module name

        Returns:
            Module instance or None
        """
        return self._modules.get(name)

    def get_provider(self, name: str) -> Optional[providers.Provider]:
        """Get a registered provider.

        Args:
            name: Provider name

        Returns:
            Provider instance or None
        """
        return self._providers.get(name)

    def list_modules(self) -> list[str]:
        """List all registered module names."""
        return list(self._modules.keys())

    def list_providers(self) -> list[str]:
        """List all registered provider names."""
        return list(self._providers.keys())


class ApplicationContainer(containers.DeclarativeContainer):
    """Base application container for services."""

    # Configuration
    config = providers.Configuration()

    # Module registry
    module_registry = providers.Singleton(ModuleRegistry)

    # Infrastructure
    infrastructure = providers.Container(
        InfrastructureContainer,
        config=config,
    )

    async def init_resources(self) -> None:
        """Initialize async resources."""
        # Override in service-specific containers
        pass

    async def shutdown_resources(self) -> None:
        """Shutdown async resources."""
        # Override in service-specific containers
        pass

    def register_module(self, module: Any, name: Optional[str] = None) -> None:
        """Register a module with the container.

        Args:
            module: Module instance to register
            name: Optional module name (defaults to module.name)
        """
        registry = self.module_registry()
        module_name = name or getattr(module, "name", module.__class__.__name__)
        registry.register_module(module_name, module)

    def get_module(self, name: str) -> Optional[Any]:
        """Get a registered module.

        Args:
            name: Module name

        Returns:
            Module instance or None
        """
        registry = self.module_registry()
        return registry.get_module(name)


class IRepository(ABC):
    """Base interface for repositories."""

    @abstractmethod
    async def create(self, entity: Any) -> Any:
        """Create an entity."""
        pass

    @abstractmethod
    async def get(self, id: str) -> Optional[Any]:
        """Get an entity by ID."""
        pass

    @abstractmethod
    async def update(self, id: str, entity: Any) -> Optional[Any]:
        """Update an entity."""
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Delete an entity."""
        pass

    @abstractmethod
    async def list(self, **filters) -> list[Any]:
        """List entities with optional filters."""
        pass


class IService(ABC):
    """Base interface for services."""

    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        """Execute service logic."""
        pass


class BaseRepository:
    """Base repository implementation with common patterns."""

    def __init__(self, db_client=None, **kwargs):
        """Initialize repository with database client."""
        self.db_client = db_client
        self._storage = {}  # Fallback in-memory storage

    async def health_check(self) -> bool:
        """Check if repository is healthy."""
        return self.db_client is not None or len(self._storage) >= 0


class BaseService:
    """Base service implementation with common patterns."""

    def __init__(self, **kwargs):
        """Initialize service with dependencies."""
        # Store all dependencies as attributes
        for key, value in kwargs.items():
            setattr(self, key, value)

    async def health_check(self) -> bool:
        """Check if service is healthy."""
        return True


class ServiceConfig:
    """Base service configuration class."""

    def __init__(self, service_name: str = "unknown"):
        """Initialize service configuration.

        Args:
            service_name: Name of the service
        """
        self.service_name = service_name
        self.version = "1.0.0"
        self.environment = "development"

        # Database config
        self.database = {
            "url": f"postgresql://localhost:5432/{service_name}_db",
        }

        # Redis config
        self.redis = {
            "host": "localhost",
            "port": 6379,
            "db": 1,
        }

        # AWS config
        self.aws = {
            "region": "us-east-1",
            "endpoint_url": "http://localhost:4566",
        }


class ContainerManager:
    """Manager for handling multiple containers."""

    def __init__(self):
        self._containers: Dict[str, ApplicationContainer] = {}

    def register(self, name: str, container: ApplicationContainer) -> None:
        """Register a container.

        Args:
            name: Container name
            container: Container instance
        """
        self._containers[name] = container

    def get(self, name: str) -> Optional[ApplicationContainer]:
        """Get a registered container.

        Args:
            name: Container name

        Returns:
            Container instance or None
        """
        return self._containers.get(name)

    def list_containers(self) -> list[str]:
        """List all registered container names."""
        return list(self._containers.keys())

    async def init_all(self) -> None:
        """Initialize all registered containers."""
        for container in self._containers.values():
            await container.init_resources()

    async def shutdown_all(self) -> None:
        """Shutdown all registered containers."""
        for container in self._containers.values():
            await container.shutdown_resources()


# Global container manager
_container_manager = ContainerManager()


def get_container_manager() -> ContainerManager:
    """Get the global container manager."""
    return _container_manager


# Dependency injection decorators
def injectable(cls: Type) -> Type:
    """Decorator to mark a class as injectable.

    Args:
        cls: Class to mark as injectable

    Returns:
        Decorated class
    """
    cls.__injectable__ = True
    return cls


def inject_container(container_name: str):
    """Decorator to inject a container into a function.

    Args:
        container_name: Name of the container to inject

    Returns:
        Decorator function
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            container = get_container_manager().get(container_name)
            if container is None:
                raise ValueError(f"Container '{container_name}' not registered")
            return func(*args, container=container, **kwargs)

        return wrapper

    return decorator
