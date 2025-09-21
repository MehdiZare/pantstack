"""Dependency injection container for auth service."""

from dependency_injector import containers, providers

from stack.libs.shared.core.config_strategy import ConfigLoader
from services.auth.lib.core.config import AuthConfig
from services.auth.lib.core.database import get_supabase_client
from services.auth.lib.core.events import EventBackbone
from services.auth.lib.core.redis import get_redis_client
from services.auth.lib.modules.auth.repositories import AuthRepository
from services.auth.lib.modules.auth.services import AuthService
from services.auth.lib.modules.users.repositories import UserRepository
from services.auth.lib.modules.users.services import UserService


class CoreContainer(containers.DeclarativeContainer):
    """Core infrastructure container."""

    # Configuration with smart loading
    config = providers.Singleton(
        ConfigLoader.load,
        config_class=AuthConfig,
        service_name="auth",
    )

    # Infrastructure clients
    supabase_client = providers.Singleton(
        get_supabase_client,
        config=config.provided.database,
    )

    redis_client = providers.Singleton(
        get_redis_client,
        config=config.provided.redis,
    )

    event_backbone = providers.Singleton(
        EventBackbone,
        config=config.provided,
        redis=redis_client,
    )


class RepositoryContainer(containers.DeclarativeContainer):
    """Repository layer container."""

    core = providers.DependenciesContainer()

    # Auth repositories
    auth_repository = providers.Factory(
        AuthRepository,
        db=core.supabase_client,
        redis=core.redis_client,
    )

    # User repositories
    user_repository = providers.Factory(
        UserRepository,
        db=core.supabase_client,
    )


class ServiceContainer(containers.DeclarativeContainer):
    """Service layer container."""

    core = providers.DependenciesContainer()
    repositories = providers.DependenciesContainer()

    # Auth service
    auth_service = providers.Factory(
        AuthService,
        auth_repo=repositories.auth_repository,
        user_repo=repositories.user_repository,
        event_backbone=core.event_backbone,
        config=core.config,
    )

    # User service
    user_service = providers.Factory(
        UserService,
        user_repo=repositories.user_repository,
        event_backbone=core.event_backbone,
        config=core.config,
    )


class AuthContainer(containers.DeclarativeContainer):
    """Main auth service container."""

    # Sub-containers
    core = providers.Container(CoreContainer)

    repositories = providers.Container(
        RepositoryContainer,
        core=core,
    )

    services = providers.Container(
        ServiceContainer,
        core=core,
        repositories=repositories,
    )

    # Wiring configuration
    wiring_config = containers.WiringConfiguration(
        modules=[
            "services.auth.src.api.routes",
            "services.auth.src.tasks.user_tasks",
            "services.auth.src.tasks.email_tasks",
        ]
    )


# Global container instance
_container: AuthContainer | None = None


def get_container() -> AuthContainer:
    """Get or create the container instance.

    Returns:
        Auth service container
    """
    global _container
    if _container is None:
        _container = AuthContainer()
        _container.wire(modules=_container.wiring_config.modules)
    return _container


def get_service_container() -> AuthContainer:
    """FastAPI dependency for getting the container.

    Returns:
        Auth service container
    """
    return get_container()