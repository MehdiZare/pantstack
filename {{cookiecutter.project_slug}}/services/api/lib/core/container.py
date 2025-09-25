"""Dependency injection container for API gateway service."""

from dependency_injector import containers, providers

from shared.core.container import ApplicationContainer as BaseApplicationContainer
from shared.core.container import (
    ContainerManager,
    InfrastructureContainer,
)


class APIConfig:
    """API service configuration."""

    def __init__(self):
        self.service_name = "api"
        self.version = "1.0.0"
        self.environment = "development"

        # API Gateway specific config
        self.cors_origins = ["*"]
        self.rate_limit = {
            "enabled": False,
            "requests_per_minute": 60,
        }

        # Service discovery
        self.service_discovery = {
            "enabled": True,
            "services": ["auth", "agent", "web"],
        }

        # Database config (for gateway-specific data)
        self.database = {
            "url": "postgresql://localhost:5432/api_db",
        }

        # Redis config (for caching/rate limiting)
        self.redis = {
            "host": "localhost",
            "port": 6379,
            "db": 0,
        }

        # AWS config
        self.aws = {
            "region": "us-east-1",
            "endpoint_url": "http://localhost:4566",
        }


class ServiceProxy:
    """Proxy for routing requests to backend services."""

    def __init__(self, service_name: str, base_url: str = None):
        self.service_name = service_name
        self.base_url = (
            base_url or f"http://localhost:800{self._get_port(service_name)}"
        )

    def _get_port(self, service_name: str) -> int:
        """Get port for a service."""
        ports = {
            "auth": 1,
            "agent": 2,
            "web": 3,
        }
        return ports.get(service_name, 0)

    async def forward(self, path: str, method: str, **kwargs):
        """Forward request to backend service."""
        # In production, this would use httpx or similar to forward requests
        return {"forwarded_to": self.service_name, "path": path, "method": method}


class GatewayService:
    """API Gateway service for request routing and aggregation."""

    def __init__(self, config: APIConfig, container_manager: ContainerManager):
        self.config = config
        self.container_manager = container_manager
        self._service_proxies = {}

    def get_service_proxy(self, service_name: str) -> ServiceProxy:
        """Get or create a service proxy."""
        if service_name not in self._service_proxies:
            self._service_proxies[service_name] = ServiceProxy(service_name)
        return self._service_proxies[service_name]

    async def route_request(self, service: str, path: str, method: str, **kwargs):
        """Route a request to the appropriate service."""
        proxy = self.get_service_proxy(service)
        return await proxy.forward(path, method, **kwargs)

    def get_service_health(self) -> dict:
        """Get health status of all services."""
        health = {}
        for service in self.config.service_discovery.get("services", []):
            # In production, this would check actual service health
            health[service] = {"status": "healthy", "uptime": "100%"}
        return health


class RateLimiter:
    """Rate limiting service."""

    def __init__(self, redis_client, config: dict):
        self.redis = redis_client
        self.config = config

    async def check_rate_limit(self, identifier: str) -> bool:
        """Check if request is within rate limit."""
        if not self.config.get("enabled"):
            return True

        # In production, implement actual rate limiting logic
        return True


class CacheService:
    """Caching service for API responses."""

    def __init__(self, redis_client):
        self.redis = redis_client

    async def get(self, key: str):
        """Get cached value."""
        # In production, implement actual cache get
        return None

    async def set(self, key: str, value: any, ttl: int = 300):
        """Set cached value."""
        # In production, implement actual cache set
        pass


class APIInfrastructureContainer(InfrastructureContainer):
    """Infrastructure container for API service."""

    config = providers.DependenciesContainer()

    # Database client (for gateway-specific data)
    database_client = providers.Singleton(
        lambda: {"connected": True},
    )

    # Redis client (for caching and rate limiting)
    redis_client = providers.Singleton(
        lambda: {"connected": True},
    )


class APIServiceContainer(containers.DeclarativeContainer):
    """Service layer container for API gateway."""

    infrastructure = providers.DependenciesContainer()
    config = providers.DependenciesContainer()

    # Container manager for service containers
    container_manager = providers.Singleton(ContainerManager)

    # Gateway service
    gateway_service = providers.Singleton(
        GatewayService,
        config=config,
        container_manager=container_manager,
    )

    # Rate limiter
    rate_limiter = providers.Singleton(
        RateLimiter,
        redis_client=infrastructure.redis_client,
        config=config.rate_limit,
    )

    # Cache service
    cache_service = providers.Singleton(
        CacheService,
        redis_client=infrastructure.redis_client,
    )


class ApplicationContainer(BaseApplicationContainer):
    """Main container for API gateway service."""

    # Configuration
    config = providers.Singleton(APIConfig)

    # Infrastructure
    infrastructure = providers.Container(
        APIInfrastructureContainer,
        config=config,
    )

    # Services
    services = providers.Container(
        APIServiceContainer,
        infrastructure=infrastructure,
        config=config,
    )

    async def init_resources(self):
        """Initialize async resources."""
        print("Initializing API Gateway resources...")

        # Register service containers
        if self.config().service_discovery.get("enabled"):
            await self._register_service_containers()

    async def _register_service_containers(self):
        """Register containers from backend services."""
        container_manager = self.services.container_manager()

        for service_name in self.config().service_discovery.get("services", []):
            try:
                # Dynamically import service containers
                if service_name == "auth":
                    from services.auth.lib.core.container import get_container as get_auth_container

                    container_manager.register("auth", get_auth_container())
                elif service_name == "agent":
                    from services.agent.lib.core.container import (
                        get_container as get_agent_container,
                    )

                    container_manager.register("agent", get_agent_container())
                elif service_name == "web":
                    from services.web.lib.core.container import get_container as get_web_container

                    container_manager.register("web", get_web_container())

                print(f"  ✅ Registered {service_name} container")
            except ImportError as e:
                print(f"  ⚠️ Could not register {service_name} container: {e}")

    async def shutdown_resources(self):
        """Shutdown async resources."""
        print("Shutting down API Gateway resources...")

        # Shutdown all registered service containers
        container_manager = self.services.container_manager()
        await container_manager.shutdown_all()


# Global container instance
_container: ApplicationContainer = None


def get_container() -> ApplicationContainer:
    """Get or create the container instance."""
    global _container
    if _container is None:
        _container = ApplicationContainer()
    return _container
