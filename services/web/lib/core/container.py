"""Dependency injection container for web service."""

from dependency_injector import containers, providers

from services.web.domain.services.jobs import JobService
from services.web.public.providers import provide_job_repo, provide_queue
from shared.core.container import ApplicationContainer as BaseApplicationContainer
from shared.core.container import (
    InfrastructureContainer,
)
from shared.core.container import RepositoryContainer as BaseRepositoryContainer
from shared.core.container import ServiceContainer as BaseServiceContainer


class WebConfig:
    """Web service configuration."""

    def __init__(self):
        self.service_name = "web"
        self.version = "0.1.0"
        self.environment = "development"

        # Database config
        self.database = {
            "url": "postgresql://localhost:5432/web_db",
        }

        # Redis config
        self.redis = {
            "host": "localhost",
            "port": 6379,
            "db": 2,
        }

        # AWS config
        self.aws = {
            "region": "us-east-1",
            "endpoint_url": "http://localhost:4566",
        }


class WebRepositoryContainer(BaseRepositoryContainer):
    """Repository layer container for web service."""

    infrastructure = providers.DependenciesContainer()

    # Job repository - using existing provider
    job_repository = providers.Factory(provide_job_repo)


class WebServiceContainer(BaseServiceContainer):
    """Service layer container for web service."""

    repositories = providers.DependenciesContainer()
    infrastructure = providers.DependenciesContainer()

    # Queue provider - using existing provider
    queue = providers.Factory(provide_queue)

    # Job service
    job_service = providers.Factory(
        JobService,
        job_repo=repositories.job_repository,
        queue=queue,
    )


class WebInfrastructureContainer(InfrastructureContainer):
    """Infrastructure container for web service."""

    config = providers.DependenciesContainer()

    # Database client
    database_client = providers.Singleton(
        lambda: {"connected": True},
    )

    # Redis client
    redis_client = providers.Singleton(
        lambda: {"connected": True},
    )

    # SQS client
    sqs_client = providers.Singleton(
        lambda: {"connected": True},
    )


class ApplicationContainer(BaseApplicationContainer):
    """Main container for web service."""

    # Configuration
    config = providers.Singleton(WebConfig)

    # Infrastructure
    infrastructure = providers.Container(
        WebInfrastructureContainer,
        config=config,
    )

    # Repositories
    repositories = providers.Container(
        WebRepositoryContainer,
        infrastructure=infrastructure,
    )

    # Services
    services = providers.Container(
        WebServiceContainer,
        repositories=repositories,
        infrastructure=infrastructure,
    )

    async def init_resources(self):
        """Initialize async resources."""
        print("Initializing Web service resources...")
        # Add initialization logic here

    async def shutdown_resources(self):
        """Shutdown async resources."""
        print("Shutting down Web service resources...")
        # Add cleanup logic here


# Global container instance
_container: ApplicationContainer = None


def get_container() -> ApplicationContainer:
    """Get or create the container instance."""
    global _container
    if _container is None:
        _container = ApplicationContainer()
    return _container
