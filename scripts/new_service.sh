#!/usr/bin/env bash
set -euo pipefail

SVC=${S:-${1:-}}
if [ -z "$SVC" ]; then
  echo "Usage: S=<name> scripts/new_service.sh" >&2
  exit 1
fi
base="services/$SVC"
if [ -d "$base" ]; then
  echo "Service '$SVC' already exists at $base"
  exit 0
fi

echo "Scaffolding service at $base"

# Create directory structure
mkdir -p "$base"/app/api "$base"/app/worker
mkdir -p "$base"/domain/models "$base"/domain/services "$base"/domain/ports
mkdir -p "$base"/adapters/repositories
mkdir -p "$base"/public
mkdir -p "$base"/lib/core
mkdir -p "$base"/infrastructure
mkdir -p "$base"/tests/unit "$base"/tests/integration

# Create __init__.py files
touch "$base"/__init__.py
touch "$base"/app/__init__.py
touch "$base"/app/api/__init__.py
touch "$base"/app/worker/__init__.py
touch "$base"/domain/__init__.py
touch "$base"/domain/models/__init__.py
touch "$base"/domain/services/__init__.py
touch "$base"/domain/ports/__init__.py
touch "$base"/adapters/__init__.py
touch "$base"/adapters/repositories/__init__.py
touch "$base"/public/__init__.py
touch "$base"/lib/__init__.py
touch "$base"/lib/core/__init__.py
touch "$base"/tests/__init__.py
touch "$base"/tests/unit/__init__.py
touch "$base"/tests/integration/__init__.py

cat > "$base"/BUILD << 'EOF'
python_sources(
    name="${name}_core",
    sources=["domain/**/*.py", "adapters/**/*.py", "public/**/*.py"],
    resolve="${name}_core",
    dependencies=[
        "stack/libs/shared",
        "stack/events/libs",
        "3rdparty/python:${name}_core_reqs",
    ],
    overrides={
        "domain/**/*.py": {
            "dependencies": [
                "3rdparty/python:${name}_core_reqs#pydantic",
            ]
        },
    },
)

python_sources(
    name="${name}_api_src",
    sources=["app/api/**/*.py"],
    resolve="${name}_api",
    dependencies=[":${name}_core", "3rdparty/python:${name}_api_reqs"],
    overrides={
        "app/api/**/*.py": {
            "dependencies": [
                "3rdparty/python:${name}_api_reqs#fastapi",
                "3rdparty/python:${name}_api_reqs#uvicorn",
                "3rdparty/python:${name}_api_reqs#pydantic",
            ]
        },
    },
)

python_sources(
    name="${name}_worker_src",
    sources=["app/worker/**/*.py"],
    resolve="${name}_core",
    dependencies=[":${name}_core"],
)

pex_binary(
    name="${name}_api_pex",
    entry_point="services.${name}.app.api.main:run",
    resolve="${name}_api",
    dependencies=[":${name}_api_src"],
)

pex_binary(
    name="${name}_worker_pex",
    entry_point="services.${name}.app.worker.run:main",
    resolve="${name}_core",
    dependencies=[":${name}_worker_src"],
)

docker_image(
    name="${name}_image",
    dependencies=[":${name}_api_pex"],
    image_tags=["latest"],
    source="Dockerfile.api",
)

docker_image(
    name="${name}_worker_image",
    dependencies=[":${name}_worker_pex"],
    image_tags=["latest"],
    source="Dockerfile.worker",
)

python_tests(
    name="unit",
    sources=["tests/unit/**/*.py"],
    resolve="${name}_api",
    dependencies=[
        ":${name}_core",
        ":${name}_api_src",
        ":${name}_worker_src",
        "3rdparty/python:${name}_api_reqs#fastapi",
        "3rdparty/python:${name}_api_reqs#httpx",
    ],
)

python_tests(
    name="integration",
    sources=["tests/integration/**/*.py"],
    resolve="${name}_api",
    dependencies=[":${name}_core"],
)
EOF

sed -i '' "s/\${name}/$SVC/g" "$base"/BUILD 2>/dev/null || sed -i "s/\${name}/$SVC/g" "$base"/BUILD

# Create DI container
cat > "$base"/lib/core/container.py << 'EOF'
"""Dependency injection container for ${name} service."""

from dependency_injector import containers, providers

from shared.core.container import (
    ApplicationContainer as BaseApplicationContainer,
    InfrastructureContainer,
    RepositoryContainer as BaseRepositoryContainer,
    ServiceContainer as BaseServiceContainer,
)


class ${NAME}Config:
    """${name} service configuration."""

    def __init__(self):
        self.service_name = "${name}"
        self.version = "1.0.0"
        self.environment = "development"

        # Database config
        self.database = {
            "url": "postgresql://localhost:5432/${name}_db",
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


class ${NAME}RepositoryContainer(BaseRepositoryContainer):
    """Repository layer container for ${name} service."""

    infrastructure = providers.DependenciesContainer()

    # Example repository (uncomment and modify as needed)
    # from services.${name}.adapters.repositories.example_repository import ExampleRepository
    # example_repository = providers.Singleton(
    #     ExampleRepository,
    #     db_client=infrastructure.database_client,
    # )


class ${NAME}ServiceContainer(BaseServiceContainer):
    """Service layer container for ${name} service."""

    repositories = providers.DependenciesContainer()
    infrastructure = providers.DependenciesContainer()

    # Example service (uncomment and modify as needed)
    # from services.${name}.domain.services.example_service import ExampleService
    # example_service = providers.Factory(
    #     ExampleService,
    #     repository=repositories.example_repository,
    # )


class ${NAME}InfrastructureContainer(InfrastructureContainer):
    """Infrastructure container for ${name} service."""

    config = providers.DependenciesContainer()

    # Database client
    database_client = providers.Singleton(
        lambda: {"connected": True},
    )

    # Redis client
    redis_client = providers.Singleton(
        lambda: {"connected": True},
    )


class ApplicationContainer(BaseApplicationContainer):
    """Main container for ${name} service."""

    # Configuration
    config = providers.Singleton(${NAME}Config)

    # Infrastructure
    infrastructure = providers.Container(
        ${NAME}InfrastructureContainer,
        config=config,
    )

    # Repositories
    repositories = providers.Container(
        ${NAME}RepositoryContainer,
        infrastructure=infrastructure,
    )

    # Services
    services = providers.Container(
        ${NAME}ServiceContainer,
        repositories=repositories,
        infrastructure=infrastructure,
    )

    async def init_resources(self):
        """Initialize async resources."""
        print("Initializing ${name} service resources...")
        # Add initialization logic here

    async def shutdown_resources(self):
        """Shutdown async resources."""
        print("Shutting down ${name} service resources...")
        # Add cleanup logic here


# Global container instance
_container: ApplicationContainer = None


def get_container() -> ApplicationContainer:
    """Get or create the container instance."""
    global _container
    if _container is None:
        _container = ApplicationContainer()
    return _container
EOF

cat > "$base"/app/api/main.py << 'EOF'
"""Main FastAPI application for ${name} service."""

from contextlib import asynccontextmanager

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, FastAPI
from structlog import get_logger

from services.${name}.lib.core.container import ApplicationContainer, get_container

logger = get_logger(__name__)

# Initialize container
container = get_container()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    logger.info("Starting ${name} Service API")
    await container.init_resources()
    container.wire(modules=[__name__])

    yield

    # Shutdown
    logger.info("Shutting down ${name} Service API")
    await container.shutdown_resources()


app = FastAPI(
    title="${name} Service",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": "${name}"}


@app.get("/")
def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "service": "${name}",
        "version": "1.0.0",
        "status": "running",
    }


# Example endpoint with dependency injection
# @app.get("/example")
# @inject
# async def example(
#     service = Depends(Provide[ApplicationContainer.services.example_service]),
# ):
#     """Example endpoint using dependency injection."""
#     return await service.do_something()


def run() -> None:
    """Run the application."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    run()
EOF

cat > "$base"/app/worker/run.py << 'EOF'
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    """Main entry point for the worker."""
    logger.info("Worker started for service: ${name}")
    # TODO: Add worker logic here


if __name__ == "__main__":
    main()
EOF

# Create example domain model
cat > "$base"/domain/models/example.py << 'EOF'
"""Example domain model."""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ExampleEntity(BaseModel):
    """Example domain entity."""

    id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: bool = True

    def validate_business_rules(self) -> bool:
        """Validate business rules for this entity."""
        # Add business logic validation here
        return True
EOF

# Create repository port
cat > "$base"/domain/ports/repository.py << 'EOF'
"""Repository port definitions."""

from typing import List, Optional, Protocol
from uuid import UUID

from services.${name}.domain.models.example import ExampleEntity


class ExampleRepositoryPort(Protocol):
    """Port for example repository."""

    async def create(self, entity: ExampleEntity) -> ExampleEntity:
        """Create an entity."""
        ...

    async def get(self, entity_id: UUID) -> Optional[ExampleEntity]:
        """Get entity by ID."""
        ...

    async def list(self) -> List[ExampleEntity]:
        """List all entities."""
        ...

    async def update(self, entity_id: UUID, entity: ExampleEntity) -> Optional[ExampleEntity]:
        """Update an entity."""
        ...

    async def delete(self, entity_id: UUID) -> bool:
        """Delete an entity."""
        ...
EOF

# Create domain service
cat > "$base"/domain/services/example_service.py << 'EOF'
"""Example domain service."""

import logging
from typing import Optional
from uuid import UUID

from services.${name}.domain.models.example import ExampleEntity
from services.${name}.domain.ports.repository import ExampleRepositoryPort

logger = logging.getLogger(__name__)


class ExampleService:
    """Service for example business logic."""

    def __init__(self, repository: ExampleRepositoryPort):
        """Initialize service.

        Args:
            repository: Example repository
        """
        self.repository = repository

    async def create_example(self, entity: ExampleEntity) -> ExampleEntity:
        """Create example with business rules validation.

        Args:
            entity: Entity to create

        Returns:
            Created entity
        """
        if not entity.validate_business_rules():
            raise ValueError("Business rules validation failed")

        created = await self.repository.create(entity)
        logger.info(f"Example created: {created.id}")
        return created

    async def get_example(self, entity_id: UUID) -> Optional[ExampleEntity]:
        """Get example by ID.

        Args:
            entity_id: Entity ID

        Returns:
            Entity if found
        """
        return await self.repository.get(entity_id)
EOF

# Create repository implementation
cat > "$base"/adapters/repositories/example_repository.py << 'EOF'
"""Example repository implementation."""

from typing import List, Optional
from uuid import UUID

from services.${name}.domain.models.example import ExampleEntity


class ExampleRepository:
    """Repository for example data."""

    def __init__(self, db_client):
        """Initialize repository.

        Args:
            db_client: Database client
        """
        self.db = db_client
        self._storage = {}  # In-memory storage for now

    async def create(self, entity: ExampleEntity) -> ExampleEntity:
        """Create an entity."""
        self._storage[entity.id] = entity
        return entity

    async def get(self, entity_id: UUID) -> Optional[ExampleEntity]:
        """Get entity by ID."""
        return self._storage.get(entity_id)

    async def list(self) -> List[ExampleEntity]:
        """List all entities."""
        return list(self._storage.values())

    async def update(self, entity_id: UUID, entity: ExampleEntity) -> Optional[ExampleEntity]:
        """Update an entity."""
        if entity_id in self._storage:
            self._storage[entity_id] = entity
            return entity
        return None

    async def delete(self, entity_id: UUID) -> bool:
        """Delete an entity."""
        if entity_id in self._storage:
            del self._storage[entity_id]
            return True
        return False
EOF

# Create Dockerfiles
cat > "$base"/Dockerfile.api << 'EOF'
FROM python:3.11-slim

WORKDIR /app

COPY . .

ENTRYPOINT ["python", "-m", "services.${name}.app.api.main"]
EOF

cat > "$base"/Dockerfile.worker << 'EOF'
FROM python:3.11-slim

WORKDIR /app

COPY . .

ENTRYPOINT ["python", "-m", "services.${name}.app.worker.run"]
EOF

# Create Pulumi infrastructure
cat > "$base"/infrastructure/Pulumi.yaml << 'EOF'
name: ${name}
runtime:
  name: python
  options:
    virtualenv: venv
backend:
  url: s3://pulumi-state-${name}
EOF

cat > "$base"/infrastructure/requirements.txt << 'EOF'
pulumi>=3.0.0
pulumi-aws>=6.0.0
EOF

cat > "$base"/infrastructure/__main__.py << 'EOF'
import os
from stack.infra.components.http_service import EcsHttpService
import pulumi

MODULE = os.getenv("MODULE", "svc")
AWS_REGION = os.getenv("AWS_REGION", "eu-west-2")
AWS_ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID", "")
PROJECT_SLUG = os.getenv("PROJECT_SLUG", "mono-template")
BRANCH = os.getenv("GITHUB_REF_NAME", "dev")
SHORT_SHA = (os.getenv("GITHUB_SHA", "") or "dev")[:7]
ECR_REPO = os.getenv("ECR_REPOSITORY", PROJECT_SLUG)
ECR_BASE = f"{AWS_ACCOUNT_ID}.dkr.ecr.{AWS_REGION}.amazonaws.com/{ECR_REPO}"

api_image = f"{ECR_BASE}:{MODULE}-{BRANCH}-{SHORT_SHA}"

svc = EcsHttpService(name=f"{MODULE}-api", image=api_image, port=8000, env={"SERVICE_NAME": MODULE})
pulumi.export("alb_dns", svc.alb_dns)
pulumi.export("url", svc.url)
EOF

# Replace ${name} and ${NAME} placeholders with actual service name
# Convert service name to PascalCase for class names (handle snake_case)
NAME=$(echo "$SVC" | awk -F_ '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) substr($i,2); print}' | tr -d ' ')
sed -i '' "s/\${name}/$SVC/g" "$base"/BUILD 2>/dev/null || sed -i "s/\${name}/$SVC/g" "$base"/BUILD
sed -i '' "s/\${name}/$SVC/g" "$base"/app/api/main.py 2>/dev/null || sed -i "s/\${name}/$SVC/g" "$base"/app/api/main.py
sed -i '' "s/\${NAME}/$NAME/g" "$base"/lib/core/container.py 2>/dev/null || sed -i "s/\${NAME}/$NAME/g" "$base"/lib/core/container.py
sed -i '' "s/\${name}/$SVC/g" "$base"/lib/core/container.py 2>/dev/null || sed -i "s/\${name}/$SVC/g" "$base"/lib/core/container.py
sed -i '' "s/\${name}/$SVC/g" "$base"/app/worker/run.py 2>/dev/null || sed -i "s/\${name}/$SVC/g" "$base"/app/worker/run.py
sed -i '' "s/\${name}/$SVC/g" "$base"/domain/ports/repository.py 2>/dev/null || sed -i "s/\${name}/$SVC/g" "$base"/domain/ports/repository.py
sed -i '' "s/\${name}/$SVC/g" "$base"/domain/services/example_service.py 2>/dev/null || sed -i "s/\${name}/$SVC/g" "$base"/domain/services/example_service.py
sed -i '' "s/\${name}/$SVC/g" "$base"/adapters/repositories/example_repository.py 2>/dev/null || sed -i "s/\${name}/$SVC/g" "$base"/adapters/repositories/example_repository.py
sed -i '' "s/\${name}/$SVC/g" "$base"/Dockerfile.api 2>/dev/null || sed -i "s/\${name}/$SVC/g" "$base"/Dockerfile.api
sed -i '' "s/\${name}/$SVC/g" "$base"/Dockerfile.worker 2>/dev/null || sed -i "s/\${name}/$SVC/g" "$base"/Dockerfile.worker
sed -i '' "s/\${name}/$SVC/g" "$base"/infrastructure/Pulumi.yaml 2>/dev/null || sed -i "s/\${name}/$SVC/g" "$base"/infrastructure/Pulumi.yaml
sed -i '' "s/\${name}/$SVC/g" "$base"/infrastructure/__main__.py 2>/dev/null || sed -i "s/\${name}/$SVC/g" "$base"/infrastructure/__main__.py

# Create requirements files
cat > "3rdparty/python/requirements-$SVC-core.txt" << 'EOF'
pydantic>=2.0.0
dependency-injector>=4.41.0
structlog>=24.1.0
EOF

cat > "3rdparty/python/requirements-$SVC-api.txt" << 'EOF'
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
pydantic>=2.0.0
httpx>=0.24.0
python-multipart>=0.0.6
dependency-injector>=4.41.0
structlog>=24.1.0
EOF

# Update pants.toml with new resolvers
if [ -f "scripts/update_pants_resolvers.sh" ]; then
  ./scripts/update_pants_resolvers.sh "$SVC"
else
  echo "\nNOTE: Remember to add the following to pants.toml under [python.resolves]:"
  echo "  ${SVC}_core = \"lockfiles/${SVC}_core.lock\""
  echo "  ${SVC}_api = \"lockfiles/${SVC}_api.lock\""
  echo ""
fi

echo ""
echo "Service '$SVC' scaffolded successfully."
echo "Next steps:"
echo "  1. Run: ./pants generate-lockfiles"
echo "  2. Run: ./pants test services/$SVC::"
