#!/usr/bin/env bash

# new_module.sh - Create a new module within a service
#
# Usage: ./scripts/new_module.sh <service> <module>
# Example: ./scripts/new_module.sh auth permissions

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check arguments
if [ $# -ne 2 ]; then
    echo -e "${RED}Error: Missing required arguments${NC}"
    echo "Usage: $0 <service> <module>"
    echo "Example: $0 auth permissions"
    exit 1
fi

SERVICE=$1
MODULE=$2
SERVICE_DIR="$PROJECT_ROOT/services/$SERVICE"
MODULE_DIR="$SERVICE_DIR/lib/modules/$MODULE"

# Create capitalized versions for class names
MODULE_CAPITALIZED=$(echo "$MODULE" | awk '{print toupper(substr($0,1,1)) substr($0,2)}')
SERVICE_CAPITALIZED=$(echo "$SERVICE" | awk '{print toupper(substr($0,1,1)) substr($0,2)}')

# Validate service exists
if [ ! -d "$SERVICE_DIR" ]; then
    echo -e "${RED}Error: Service '$SERVICE' does not exist${NC}"
    echo "Available services:"
    ls -1 "$PROJECT_ROOT/services"
    exit 1
fi

# Check if module already exists
if [ -d "$MODULE_DIR" ]; then
    echo -e "${YELLOW}Warning: Module '$MODULE' already exists in service '$SERVICE'${NC}"
    read -p "Overwrite existing module? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    rm -rf "$MODULE_DIR"
fi

echo -e "${GREEN}Creating module '$MODULE' in service '$SERVICE'...${NC}"

# Create module directory structure
mkdir -p "$MODULE_DIR/tests"

# Create __init__.py
cat > "$MODULE_DIR/__init__.py" << EOF
"""${MODULE_CAPITALIZED} module for $SERVICE service."""

from .module import ${MODULE_CAPITALIZED}Module

__all__ = ["${MODULE_CAPITALIZED}Module"]
EOF

# Create module.py
cat > "$MODULE_DIR/module.py" << EOF
"""${MODULE_CAPITALIZED} module interface."""

from typing import List, Optional, Dict, Any

from dependency_injector import containers, providers
from fastapi import APIRouter

from shared.core.container import BaseRepository, BaseService
from .routes import router
from .tasks import task_registry
from .handlers import event_handlers
from .schemas import ${MODULE_CAPITALIZED}Config
from .repository import ${MODULE_CAPITALIZED}Repository
from .service import ${MODULE_CAPITALIZED}Service


class ${MODULE_CAPITALIZED}ModuleContainer(containers.DeclarativeContainer):
    """Dependency injection container for ${MODULE} module."""

    # Configuration
    config = providers.Singleton(${MODULE_CAPITALIZED}Config)

    # External dependencies (will be wired by service container)
    db_client = providers.Dependency()
    redis_client = providers.Dependency()

    # Repository
    repository = providers.Singleton(
        ${MODULE_CAPITALIZED}Repository,
        db_client=db_client,
    )

    # Service
    service = providers.Factory(
        ${MODULE_CAPITALIZED}Service,
        repository=repository,
        config=config,
    )


class ${MODULE_CAPITALIZED}Module:
    """${MODULE_CAPITALIZED} module implementation."""

    def __init__(self, config: Optional[${MODULE_CAPITALIZED}Config] = None):
        """Initialize the ${MODULE} module.

        Args:
            config: Optional module configuration
        """
        self.name = "${MODULE}"
        self.config = config or ${MODULE_CAPITALIZED}Config()
        self._router = router
        self._tasks = task_registry
        self._handlers = event_handlers

        # Initialize DI container
        self.container = ${MODULE_CAPITALIZED}ModuleContainer()
        if config:
            self.container.config.override(config)

    @property
    def display_name(self) -> str:
        """Get the display name of the module."""
        return self.name.replace("_", " ").title()

    def get_routes(self) -> APIRouter:
        """Get the FastAPI router for this module.

        Returns:
            FastAPI router with all module endpoints
        """
        return self._router

    def get_tasks(self) -> List[str]:
        """Get the list of Celery tasks for this module.

        Returns:
            List of task names
        """
        return self._tasks

    def get_handlers(self) -> Dict[str, Any]:
        """Get the event handlers for this module.

        Returns:
            Dictionary of event types to handler functions
        """
        return self._handlers

    def get_providers(self) -> Dict[str, Any]:
        """Get the DI providers for this module.

        Returns:
            Dictionary of provider names to providers
        """
        return {
            "repository": self.container.repository,
            "service": self.container.service,
        }

    def wire_dependencies(self, **dependencies) -> None:
        """Wire external dependencies to module container.

        Args:
            **dependencies: External dependencies to wire
        """
        if "db_client" in dependencies:
            self.container.db_client.override(dependencies["db_client"])
        if "redis_client" in dependencies:
            self.container.redis_client.override(dependencies["redis_client"])

    def initialize(self) -> None:
        """Initialize module resources."""
        # Add any initialization logic here
        pass

    def shutdown(self) -> None:
        """Clean up module resources."""
        # Add any cleanup logic here
        pass
EOF

# Create routes.py
cat > "$MODULE_DIR/routes.py" << EOF
"""API routes for ${MODULE} module."""

from typing import Dict, Any, List

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status

from .schemas import (
    ${MODULE_CAPITALIZED}Request,
    ${MODULE_CAPITALIZED}Response,
    ${MODULE_CAPITALIZED}Error,
    ${MODULE_CAPITALIZED}Entity,
)
from .service import ${MODULE_CAPITALIZED}Service

router = APIRouter(prefix="/${MODULE}", tags=["${MODULE}"])


@router.get("/", response_model=${MODULE_CAPITALIZED}Response)
async def get_${MODULE}_info() -> ${MODULE_CAPITALIZED}Response:
    """Get ${MODULE} module information.

    Returns:
        Module information and status
    """
    return ${MODULE_CAPITALIZED}Response(
        module="${MODULE}",
        status="active",
        message="${MODULE_CAPITALIZED} module is running",
    )


@router.post("/", response_model=${MODULE_CAPITALIZED}Response)
@inject
async def process_${MODULE}_request(
    request: ${MODULE_CAPITALIZED}Request,
    service: ${MODULE_CAPITALIZED}Service = Depends(Provide["${MODULE}_service"]),
) -> ${MODULE_CAPITALIZED}Response:
    """Process a ${MODULE} request.

    Args:
        request: The ${MODULE} request data
        service: Injected ${MODULE} service

    Returns:
        Processing result

    Raises:
        HTTPException: If processing fails
    """
    try:
        response = await service.process_request(request)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=${MODULE_CAPITALIZED}Error(
                code="PROCESSING_ERROR",
                message=f"Failed to process ${MODULE} request: {str(e)}",
            ).model_dump(),
        )


@router.post("/entities", response_model=${MODULE_CAPITALIZED}Entity, status_code=status.HTTP_201_CREATED)
@inject
async def create_${MODULE}_entity(
    entity_data: Dict[str, Any],
    service: ${MODULE_CAPITALIZED}Service = Depends(Provide["${MODULE}_service"]),
) -> ${MODULE_CAPITALIZED}Entity:
    """Create a new ${MODULE} entity.

    Args:
        entity_data: Entity data
        service: Injected ${MODULE} service

    Returns:
        Created entity

    Raises:
        HTTPException: If creation fails
    """
    try:
        entity = await service.create_entity(entity_data)
        return entity
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create ${MODULE} entity: {str(e)}",
        )


@router.get("/entities/{entity_id}", response_model=${MODULE_CAPITALIZED}Entity)
@inject
async def get_${MODULE}_entity(
    entity_id: str,
    service: ${MODULE_CAPITALIZED}Service = Depends(Provide["${MODULE}_service"]),
) -> ${MODULE_CAPITALIZED}Entity:
    """Get a ${MODULE} entity by ID.

    Args:
        entity_id: Entity ID
        service: Injected ${MODULE} service

    Returns:
        Entity data

    Raises:
        HTTPException: If entity not found
    """
    entity = await service.get_entity(entity_id)
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"${MODULE_CAPITALIZED} entity {entity_id} not found",
        )
    return entity


@router.get("/entities", response_model=List[${MODULE_CAPITALIZED}Entity])
@inject
async def list_${MODULE}_entities(
    service: ${MODULE_CAPITALIZED}Service = Depends(Provide["${MODULE}_service"]),
) -> List[${MODULE_CAPITALIZED}Entity]:
    """List all ${MODULE} entities.

    Args:
        service: Injected ${MODULE} service

    Returns:
        List of entities
    """
    return await service.list_entities()


@router.put("/entities/{entity_id}", response_model=${MODULE_CAPITALIZED}Entity)
@inject
async def update_${MODULE}_entity(
    entity_id: str,
    entity_data: Dict[str, Any],
    service: ${MODULE_CAPITALIZED}Service = Depends(Provide["${MODULE}_service"]),
) -> ${MODULE_CAPITALIZED}Entity:
    """Update a ${MODULE} entity.

    Args:
        entity_id: Entity ID
        entity_data: Updated entity data
        service: Injected ${MODULE} service

    Returns:
        Updated entity

    Raises:
        HTTPException: If entity not found or update fails
    """
    try:
        entity = await service.update_entity(entity_id, entity_data)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"${MODULE_CAPITALIZED} entity {entity_id} not found",
            )
        return entity
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update ${MODULE} entity: {str(e)}",
        )


@router.delete("/entities/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_${MODULE}_entity(
    entity_id: str,
    service: ${MODULE_CAPITALIZED}Service = Depends(Provide["${MODULE}_service"]),
) -> None:
    """Delete a ${MODULE} entity.

    Args:
        entity_id: Entity ID
        service: Injected ${MODULE} service

    Raises:
        HTTPException: If entity not found
    """
    deleted = await service.delete_entity(entity_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"${MODULE_CAPITALIZED} entity {entity_id} not found",
        )
EOF

# Create tasks.py
cat > "$MODULE_DIR/tasks.py" << EOF
"""Celery tasks for ${MODULE} module."""

from typing import Dict, Any
from celery import shared_task


# Task registry for module discovery
task_registry = [
    "${SERVICE}.${MODULE}.process_async",
    "${SERVICE}.${MODULE}.cleanup",
    "${SERVICE}.${MODULE}.sync_data",
]


@shared_task(name="${SERVICE}.${MODULE}.process_async")
def process_${MODULE}_async(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process ${MODULE} data asynchronously.

    Args:
        data: Data to process

    Returns:
        Processing result
    """
    # TODO: Implement async processing logic
    return {
        "task": "process_${MODULE}_async",
        "status": "completed",
        "data": data,
    }


@shared_task(name="${SERVICE}.${MODULE}.cleanup")
def cleanup_${MODULE}_data(days: int = 30) -> Dict[str, Any]:
    """Clean up old ${MODULE} data.

    Args:
        days: Number of days to retain data

    Returns:
        Cleanup statistics
    """
    # TODO: Implement cleanup logic
    return {
        "task": "cleanup_${MODULE}_data",
        "status": "completed",
        "cleaned": 0,
    }


@shared_task(name="${SERVICE}.${MODULE}.sync_data")
def sync_${MODULE}_data() -> Dict[str, Any]:
    """Synchronize ${MODULE} data.

    Returns:
        Sync statistics
    """
    # TODO: Implement sync logic
    return {
        "task": "sync_${MODULE}_data",
        "status": "completed",
        "synced": 0,
    }
EOF

# Create handlers.py
cat > "$MODULE_DIR/handlers.py" << EOF
"""Event handlers for ${MODULE} module."""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# Event handler registry for module discovery
event_handlers = {
    "${SERVICE}.${MODULE}.created": handle_${MODULE}_created,
    "${SERVICE}.${MODULE}.updated": handle_${MODULE}_updated,
    "${SERVICE}.${MODULE}.deleted": handle_${MODULE}_deleted,
}


async def handle_${MODULE}_created(event: Dict[str, Any]) -> None:
    """Handle ${MODULE} created event.

    Args:
        event: Event data
    """
    logger.info(f"Handling ${MODULE} created event: {event}")
    # TODO: Implement event handling logic


async def handle_${MODULE}_updated(event: Dict[str, Any]) -> None:
    """Handle ${MODULE} updated event.

    Args:
        event: Event data
    """
    logger.info(f"Handling ${MODULE} updated event: {event}")
    # TODO: Implement event handling logic


async def handle_${MODULE}_deleted(event: Dict[str, Any]) -> None:
    """Handle ${MODULE} deleted event.

    Args:
        event: Event data
    """
    logger.info(f"Handling ${MODULE} deleted event: {event}")
    # TODO: Implement event handling logic
EOF

# Create schemas.py
cat > "$MODULE_DIR/schemas.py" << EOF
"""Data models for ${MODULE} module."""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ${MODULE_CAPITALIZED}Config(BaseModel):
    """Configuration for ${MODULE} module."""

    enabled: bool = True
    max_retries: int = 3
    timeout: int = 30
    cache_ttl: int = 300


class ${MODULE_CAPITALIZED}Request(BaseModel):
    """Request model for ${MODULE} operations."""

    id: str = Field(..., description="Unique request ID")
    data: Dict[str, Any] = Field(..., description="Request data")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional metadata"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Request timestamp"
    )


class ${MODULE_CAPITALIZED}Response(BaseModel):
    """Response model for ${MODULE} operations."""

    module: str = Field(..., description="Module name")
    status: str = Field(..., description="Response status")
    message: Optional[str] = Field(default=None, description="Status message")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Response data")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )


class ${MODULE_CAPITALIZED}Error(BaseModel):
    """Error model for ${MODULE} operations."""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(
        default=None, description="Error details"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Error timestamp"
    )


class ${MODULE_CAPITALIZED}Entity(BaseModel):
    """Domain entity for ${MODULE}."""

    id: str = Field(..., description="Entity ID")
    name: str = Field(..., description="Entity name")
    type: str = Field(default="${MODULE}", description="Entity type")
    attributes: Dict[str, Any] = Field(
        default_factory=dict, description="Entity attributes"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: Optional[datetime] = Field(
        default=None, description="Last update timestamp"
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "${MODULE}_entity_1",
                "type": "${MODULE}",
                "attributes": {"key": "value"},
                "created_at": "2024-01-01T00:00:00Z",
            }
        }
EOF

# Create repository.py
cat > "$MODULE_DIR/repository.py" << EOF
"""Repository for ${MODULE} module."""

from typing import List, Optional, Dict, Any
from uuid import UUID

from shared.core.container import BaseRepository
from .schemas import ${MODULE_CAPITALIZED}Entity


class ${MODULE_CAPITALIZED}Repository(BaseRepository):
    """Repository for ${MODULE} data operations."""

    def __init__(self, db_client=None, **kwargs):
        """Initialize repository.

        Args:
            db_client: Database client
        """
        super().__init__(db_client=db_client, **kwargs)

    async def create(self, entity: ${MODULE_CAPITALIZED}Entity) -> ${MODULE_CAPITALIZED}Entity:
        """Create a ${MODULE} entity.

        Args:
            entity: Entity to create

        Returns:
            Created entity
        """
        # For now, use in-memory storage
        entity_dict = entity.model_dump()
        self._storage[entity.id] = entity_dict
        return entity

    async def get(self, entity_id: str) -> Optional[${MODULE_CAPITALIZED}Entity]:
        """Get a ${MODULE} entity by ID.

        Args:
            entity_id: Entity ID

        Returns:
            Entity if found, None otherwise
        """
        entity_dict = self._storage.get(entity_id)
        if entity_dict:
            return ${MODULE_CAPITALIZED}Entity(**entity_dict)
        return None

    async def update(self, entity_id: str, entity: ${MODULE_CAPITALIZED}Entity) -> Optional[${MODULE_CAPITALIZED}Entity]:
        """Update a ${MODULE} entity.

        Args:
            entity_id: Entity ID
            entity: Updated entity data

        Returns:
            Updated entity if found, None otherwise
        """
        if entity_id in self._storage:
            entity_dict = entity.model_dump()
            entity_dict['id'] = entity_id
            self._storage[entity_id] = entity_dict
            return ${MODULE_CAPITALIZED}Entity(**entity_dict)
        return None

    async def delete(self, entity_id: str) -> bool:
        """Delete a ${MODULE} entity.

        Args:
            entity_id: Entity ID

        Returns:
            True if deleted, False if not found
        """
        if entity_id in self._storage:
            del self._storage[entity_id]
            return True
        return False

    async def list(self, **filters) -> List[${MODULE_CAPITALIZED}Entity]:
        """List ${MODULE} entities with optional filters.

        Args:
            **filters: Optional filters

        Returns:
            List of entities
        """
        entities = []
        for entity_dict in self._storage.values():
            entity = ${MODULE_CAPITALIZED}Entity(**entity_dict)
            # Apply filters if any
            match = True
            for key, value in filters.items():
                if hasattr(entity, key) and getattr(entity, key) != value:
                    match = False
                    break
            if match:
                entities.append(entity)
        return entities
EOF

# Create service.py
cat > "$MODULE_DIR/service.py" << EOF
"""Business logic service for ${MODULE} module."""

from typing import List, Optional, Dict, Any
import logging

from shared.core.container import BaseService
from .repository import ${MODULE_CAPITALIZED}Repository
from .schemas import ${MODULE_CAPITALIZED}Entity, ${MODULE_CAPITALIZED}Config, ${MODULE_CAPITALIZED}Request, ${MODULE_CAPITALIZED}Response

logger = logging.getLogger(__name__)


class ${MODULE_CAPITALIZED}Service(BaseService):
    """Business logic service for ${MODULE} operations."""

    def __init__(self, repository: ${MODULE_CAPITALIZED}Repository, config: ${MODULE_CAPITALIZED}Config, **kwargs):
        """Initialize service.

        Args:
            repository: ${MODULE_CAPITALIZED} repository
            config: Module configuration
        """
        super().__init__(**kwargs)
        self.repository = repository
        self.config = config

    async def process_request(self, request: ${MODULE_CAPITALIZED}Request) -> ${MODULE_CAPITALIZED}Response:
        """Process a ${MODULE} request.

        Args:
            request: Request to process

        Returns:
            Processing response
        """
        try:
            # Example business logic
            processed_data = await self._process_business_logic(request.data)

            return ${MODULE_CAPITALIZED}Response(
                module="${MODULE}",
                status="success",
                message="Request processed successfully",
                data=processed_data,
            )
        except Exception as e:
            logger.error(f"Error processing ${MODULE} request: {e}")
            return ${MODULE_CAPITALIZED}Response(
                module="${MODULE}",
                status="error",
                message=f"Processing failed: {str(e)}",
            )

    async def create_entity(self, entity_data: Dict[str, Any]) -> ${MODULE_CAPITALIZED}Entity:
        """Create a new ${MODULE} entity.

        Args:
            entity_data: Entity data

        Returns:
            Created entity
        """
        entity = ${MODULE_CAPITALIZED}Entity(**entity_data)

        # Apply business rules
        if not await self._validate_business_rules(entity):
            raise ValueError("Business rules validation failed")

        created_entity = await self.repository.create(entity)
        logger.info(f"Created ${MODULE} entity: {created_entity.id}")
        return created_entity

    async def get_entity(self, entity_id: str) -> Optional[${MODULE_CAPITALIZED}Entity]:
        """Get a ${MODULE} entity by ID.

        Args:
            entity_id: Entity ID

        Returns:
            Entity if found
        """
        return await self.repository.get(entity_id)

    async def list_entities(self, **filters) -> List[${MODULE_CAPITALIZED}Entity]:
        """List ${MODULE} entities.

        Args:
            **filters: Optional filters

        Returns:
            List of entities
        """
        return await self.repository.list(**filters)

    async def update_entity(self, entity_id: str, entity_data: Dict[str, Any]) -> Optional[${MODULE_CAPITALIZED}Entity]:
        """Update a ${MODULE} entity.

        Args:
            entity_id: Entity ID
            entity_data: Updated entity data

        Returns:
            Updated entity if found
        """
        entity = ${MODULE_CAPITALIZED}Entity(**entity_data)

        # Apply business rules
        if not await self._validate_business_rules(entity):
            raise ValueError("Business rules validation failed")

        updated_entity = await self.repository.update(entity_id, entity)
        if updated_entity:
            logger.info(f"Updated ${MODULE} entity: {entity_id}")
        return updated_entity

    async def delete_entity(self, entity_id: str) -> bool:
        """Delete a ${MODULE} entity.

        Args:
            entity_id: Entity ID

        Returns:
            True if deleted
        """
        deleted = await self.repository.delete(entity_id)
        if deleted:
            logger.info(f"Deleted ${MODULE} entity: {entity_id}")
        return deleted

    async def _process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process core business logic.

        Args:
            data: Input data

        Returns:
            Processed data
        """
        # Implement your business logic here
        return {
            "processed": True,
            "original_data": data,
            "processing_time": "2024-01-01T00:00:00Z",
        }

    async def _validate_business_rules(self, entity: ${MODULE_CAPITALIZED}Entity) -> bool:
        """Validate business rules for entity.

        Args:
            entity: Entity to validate

        Returns:
            True if valid
        """
        # Implement business rule validation here
        if not entity.name or len(entity.name) < 1:
            return False
        return True
EOF

# Create tests/__init__.py
cat > "$MODULE_DIR/tests/__init__.py" << EOF
"""Tests for ${MODULE} module."""
EOF

# Create tests/test_module.py
cat > "$MODULE_DIR/tests/test_module.py" << EOF
"""Unit tests for ${MODULE} module."""

import pytest
from unittest.mock import Mock, patch

from ..module import ${MODULE_CAPITALIZED}Module
from ..schemas import ${MODULE_CAPITALIZED}Config, ${MODULE_CAPITALIZED}Request, ${MODULE_CAPITALIZED}Response


class Test${MODULE_CAPITALIZED}Module:
    """Tests for ${MODULE_CAPITALIZED}Module class."""

    def test_module_initialization(self):
        """Test module initialization."""
        module = ${MODULE_CAPITALIZED}Module()
        assert module.name == "${MODULE}"
        assert module.display_name == "${MODULE_CAPITALIZED}".replace("_", " ").title()

    def test_module_with_config(self):
        """Test module initialization with custom config."""
        config = ${MODULE_CAPITALIZED}Config(enabled=False, max_retries=5)
        module = ${MODULE_CAPITALIZED}Module(config=config)
        assert module.config.enabled is False
        assert module.config.max_retries == 5

    def test_get_routes(self):
        """Test getting module routes."""
        module = ${MODULE_CAPITALIZED}Module()
        router = module.get_routes()
        assert router is not None
        assert router.prefix == "/${MODULE}"

    def test_get_tasks(self):
        """Test getting module tasks."""
        module = ${MODULE_CAPITALIZED}Module()
        tasks = module.get_tasks()
        assert isinstance(tasks, list)
        assert "${SERVICE}.${MODULE}.process_async" in tasks

    def test_get_handlers(self):
        """Test getting module event handlers."""
        module = ${MODULE_CAPITALIZED}Module()
        handlers = module.get_handlers()
        assert isinstance(handlers, dict)
        assert "${SERVICE}.${MODULE}.created" in handlers


@pytest.mark.asyncio
class Test${MODULE_CAPITALIZED}Routes:
    """Tests for ${MODULE} API routes."""

    async def test_get_info_endpoint(self, client):
        """Test GET /${MODULE}/ endpoint."""
        response = await client.get("/${MODULE}/")
        assert response.status_code == 200
        data = response.json()
        assert data["module"] == "${MODULE}"
        assert data["status"] == "active"

    async def test_post_request_endpoint(self, client):
        """Test POST /${MODULE}/ endpoint."""
        request_data = {
            "id": "test-123",
            "data": {"key": "value"},
        }
        response = await client.post("/${MODULE}/", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["module"] == "${MODULE}"
        assert data["status"] == "success"


class Test${MODULE_CAPITALIZED}Tasks:
    """Tests for ${MODULE} Celery tasks."""

    def test_process_async_task(self):
        """Test async processing task."""
        from ..tasks import process_${MODULE}_async

        result = process_${MODULE}_async({"test": "data"})
        assert result["status"] == "completed"
        assert result["data"] == {"test": "data"}

    def test_cleanup_task(self):
        """Test cleanup task."""
        from ..tasks import cleanup_${MODULE}_data

        result = cleanup_${MODULE}_data(days=7)
        assert result["status"] == "completed"
        assert "cleaned" in result


class Test${MODULE_CAPITALIZED}Schemas:
    """Tests for ${MODULE} data models."""

    def test_request_model(self):
        """Test request model validation."""
        request = ${MODULE_CAPITALIZED}Request(
            id="test-123",
            data={"key": "value"},
        )
        assert request.id == "test-123"
        assert request.data == {"key": "value"}

    def test_response_model(self):
        """Test response model validation."""
        response = ${MODULE_CAPITALIZED}Response(
            module="${MODULE}",
            status="success",
            message="Operation completed",
        )
        assert response.module == "${MODULE}"
        assert response.status == "success"

    def test_error_model(self):
        """Test error model validation."""
        from ..schemas import ${MODULE_CAPITALIZED}Error

        error = ${MODULE_CAPITALIZED}Error(
            code="VALIDATION_ERROR",
            message="Invalid input data",
        )
        assert error.code == "VALIDATION_ERROR"
        assert error.message == "Invalid input data"
EOF

# Update service's lib/__init__.py to include the new module
SERVICE_LIB_INIT="$SERVICE_DIR/lib/__init__.py"
if [ ! -f "$SERVICE_LIB_INIT" ]; then
    cat > "$SERVICE_LIB_INIT" << EOF
"""Service library modules."""

from .modules.${MODULE} import ${MODULE_CAPITALIZED}Module

# Module registry for service discovery
MODULES = [
    ${MODULE_CAPITALIZED}Module(),
]

__all__ = ["MODULES", "${MODULE_CAPITALIZED}Module"]
EOF
else
    echo -e "${YELLOW}Note: Remember to add ${MODULE_CAPITALIZED}Module to $SERVICE_LIB_INIT${NC}"
fi

# Create BUILD file for the module
cat > "$MODULE_DIR/BUILD" << EOF
python_sources(
    name="${MODULE}",
    resolve="${SERVICE}_core",
    dependencies=[
        "//services/${SERVICE}/domain:domain",
        "//shared/core:core",
        "//3rdparty/python:${SERVICE}_core",
    ],
)

python_tests(
    name="tests",
    resolve="test",
    dependencies=[
        ":${MODULE}",
        "//shared/tests:test_utils",
    ],
    tags=["unit", "${SERVICE}", "${MODULE}"],
)
EOF

echo -e "${GREEN}✅ Module '$MODULE' created successfully in service '$SERVICE'${NC}"
echo
echo "Next steps:"
echo "1. Register the module in $SERVICE_DIR/lib/__init__.py"
echo "2. Implement module logic in $MODULE_DIR/"
echo "3. Add module-specific dependencies to 3rdparty/python/requirements-${SERVICE}-core.txt"
echo "4. Run tests: pants test services/${SERVICE}/lib/modules/${MODULE}::"
echo "5. Format code: pants fmt services/${SERVICE}/lib/modules/${MODULE}::"
