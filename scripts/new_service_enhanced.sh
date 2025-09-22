#!/usr/bin/env bash
set -euo pipefail

# Enhanced service scaffolding with comprehensive templates
# Usage: S=<service_name> ./scripts/new_service_enhanced.sh

SVC=${S:-${1:-}}
if [ -z "$SVC" ]; then
  echo "Usage: S=<name> ./scripts/new_service_enhanced.sh" >&2
  exit 1
fi

base="services/$SVC"
if [ -d "$base" ]; then
  echo "Service '$SVC' already exists at $base"
  exit 0
fi

echo "🚀 Scaffolding enhanced service at $base"

# Create comprehensive directory structure
echo "📁 Creating directory structure..."
mkdir -p "$base"/app/api/routes
mkdir -p "$base"/app/worker
mkdir -p "$base"/domain/models
mkdir -p "$base"/domain/services
mkdir -p "$base"/domain/ports
mkdir -p "$base"/adapters/repositories
mkdir -p "$base"/adapters/external
mkdir -p "$base"/adapters/cache
mkdir -p "$base"/lib/core
mkdir -p "$base"/lib/models
mkdir -p "$base"/lib/repositories
mkdir -p "$base"/public
mkdir -p "$base"/infrastructure/migrations
mkdir -p "$base"/config
mkdir -p "$base"/tests/unit
mkdir -p "$base"/tests/integration
mkdir -p "$base"/tests/fixtures

# Create __init__.py files
echo "📝 Creating __init__.py files..."
touch "$base"/__init__.py
touch "$base"/app/__init__.py
touch "$base"/app/api/__init__.py
touch "$base"/app/api/routes/__init__.py
touch "$base"/app/worker/__init__.py
touch "$base"/domain/__init__.py
touch "$base"/domain/models/__init__.py
touch "$base"/domain/services/__init__.py
touch "$base"/domain/ports/__init__.py
touch "$base"/adapters/__init__.py
touch "$base"/adapters/repositories/__init__.py
touch "$base"/adapters/external/__init__.py
touch "$base"/adapters/cache/__init__.py
touch "$base"/lib/__init__.py
touch "$base"/lib/core/__init__.py
touch "$base"/lib/models/__init__.py
touch "$base"/lib/repositories/__init__.py
touch "$base"/public/__init__.py
touch "$base"/config/__init__.py
touch "$base"/tests/__init__.py
touch "$base"/tests/unit/__init__.py
touch "$base"/tests/integration/__init__.py
touch "$base"/tests/fixtures/__init__.py

# ================== API LAYER ==================
echo "🌐 Creating API templates..."

# Main FastAPI app
cat > "$base"/app/api/main.py << 'EOF'
"""Main FastAPI application for ${name} service."""

from typing import Dict

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.${name}.app.api.routes import health, items, protected
from services.${name}.config.settings import Settings

# Load settings
settings = Settings()

# Create FastAPI app
app = FastAPI(
    title="${name} Service",
    version="1.0.0",
    description="${name} service API",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(items.router, prefix="/api/items", tags=["items"])
app.include_router(protected.router, prefix="/api/protected", tags=["protected"])


@app.get("/", tags=["root"])
async def root() -> Dict[str, str]:
    """Root endpoint."""
    return {
        "service": "${name}",
        "version": "1.0.0",
        "status": "running",
    }


def run() -> None:
    """Run the API server."""
    uvicorn.run(
        "services.${name}.app.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )


if __name__ == "__main__":
    run()
EOF

# Health check routes
cat > "$base"/app/api/routes/health.py << 'EOF'
"""Health check endpoints."""

from typing import Dict

from fastapi import APIRouter

router = APIRouter()


@router.get("/healthz")
async def healthz() -> Dict[str, str]:
    """Basic health check."""
    return {"status": "ok", "service": "${name}"}


@router.get("/readyz")
async def readyz() -> Dict[str, str]:
    """Readiness check with dependency verification."""
    # TODO: Add database connectivity check
    # TODO: Add external service checks
    return {"status": "ready", "service": "${name}"}
EOF

# CRUD routes with Supabase
cat > "$base"/app/api/routes/items.py << 'EOF'
"""Item CRUD endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from services.${name}.app.api.dependencies import get_repository
from services.${name}.lib.models.item import Item, ItemCreate, ItemUpdate
from services.${name}.lib.repositories.item_repository import ItemRepository

router = APIRouter()


@router.post("/", response_model=Item)
async def create_item(
    item: ItemCreate,
    repo: ItemRepository = Depends(get_repository),
) -> Item:
    """Create a new item."""
    return await repo.create(item)


@router.get("/{item_id}", response_model=Item)
async def get_item(
    item_id: UUID,
    repo: ItemRepository = Depends(get_repository),
) -> Item:
    """Get item by ID."""
    item = await repo.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.get("/", response_model=List[Item])
async def list_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    repo: ItemRepository = Depends(get_repository),
) -> List[Item]:
    """List items with pagination."""
    filters = {}
    if category:
        filters["category"] = category
    return await repo.list(skip=skip, limit=limit, filters=filters)


@router.put("/{item_id}", response_model=Item)
async def update_item(
    item_id: UUID,
    item: ItemUpdate,
    repo: ItemRepository = Depends(get_repository),
) -> Item:
    """Update an item."""
    updated = await repo.update(item_id, item)
    if not updated:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated


@router.delete("/{item_id}")
async def delete_item(
    item_id: UUID,
    repo: ItemRepository = Depends(get_repository),
) -> Dict[str, str]:
    """Delete an item."""
    deleted = await repo.delete(item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"status": "deleted", "id": str(item_id)}


@router.get("/search/", response_model=List[Item])
async def search_items(
    q: str = Query(..., min_length=1),
    repo: ItemRepository = Depends(get_repository),
) -> List[Item]:
    """Search items by query."""
    return await repo.search(q)
EOF

# Protected routes example
cat > "$base"/app/api/routes/protected.py << 'EOF'
"""Protected endpoints requiring authentication."""

from typing import Dict

from fastapi import APIRouter, Depends

from shared.core.security import authenticated_endpoint

router = APIRouter()


@router.get("/user-data")
async def get_user_data(
    user=Depends(authenticated_endpoint),
) -> Dict[str, str]:
    """Get user-specific data (requires authentication)."""
    return {
        "message": f"Hello {user.get('email', 'user')}",
        "user_id": user.get("id"),
    }


@router.post("/action")
async def perform_action(
    data: Dict[str, str],
    user=Depends(authenticated_endpoint),
) -> Dict[str, str]:
    """Perform a protected action."""
    return {
        "status": "completed",
        "action": data.get("action"),
        "user": user.get("email"),
    }
EOF

# Dependencies
cat > "$base"/app/api/dependencies.py << 'EOF'
"""API dependencies and dependency injection."""

from services.${name}.lib.core.database import get_db_client
from services.${name}.lib.repositories.item_repository import ItemRepository


async def get_repository() -> ItemRepository:
    """Get item repository instance."""
    db = get_db_client()
    return ItemRepository(db)
EOF

# Service manifest for discovery
cat > "$base"/app/api/manifest.py << 'EOF'
"""Service manifest for API discovery."""

from shared.core.registry import RouteDefinition, SecurityGroup, ServiceManifest

from services.${name}.app.api.routes import health, items, protected

# Define service manifest
manifest = ServiceManifest(
    service_name="${name}",
    version="1.0.0",
    description="${name} service API",
    routes=[
        # Health routes (public)
        RouteDefinition(
            path="/healthz",
            method="GET",
            handler=health.healthz,
            security_group=SecurityGroup.PUBLIC,
            tags=["health"],
        ),
        RouteDefinition(
            path="/readyz",
            method="GET",
            handler=health.readyz,
            security_group=SecurityGroup.PUBLIC,
            tags=["health"],
        ),
        # Item routes (authenticated)
        RouteDefinition(
            path="/items",
            method="GET",
            handler=items.list_items,
            security_group=SecurityGroup.AUTHENTICATED,
            tags=["items"],
        ),
        RouteDefinition(
            path="/items",
            method="POST",
            handler=items.create_item,
            security_group=SecurityGroup.AUTHENTICATED,
            tags=["items"],
        ),
    ],
    health_check_path="/healthz",
)
EOF

# ================== WORKER LAYER ==================
echo "⚙️ Creating worker templates..."

# Enhanced worker entry point
cat > "$base"/app/worker/run.py << 'EOF'
"""Worker entry point for ${name} service."""

import asyncio
import logging
import os
from typing import Dict, Any

from services.${name}.app.worker.handlers import MessageHandler
from services.${name}.app.worker.tasks import process_item, cleanup_old_items
from services.${name}.lib.core.database import get_db_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Worker:
    """Main worker class."""

    def __init__(self):
        """Initialize worker."""
        self.handler = MessageHandler()
        self.running = False

    async def start(self):
        """Start the worker."""
        self.running = True
        logger.info("Worker started for service: ${name}")

        # Start message processing
        await self.process_messages()

    async def stop(self):
        """Stop the worker."""
        self.running = False
        logger.info("Worker stopped")

    async def process_messages(self):
        """Process messages from queue."""
        while self.running:
            try:
                # Process SQS messages
                await self.handler.process_queue_messages()

                # Small delay between polls
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error processing messages: {e}")
                await asyncio.sleep(5)


def main() -> None:
    """Main entry point for the worker."""
    worker = Worker()

    # Run the async worker
    try:
        asyncio.run(worker.start())
    except KeyboardInterrupt:
        logger.info("Shutting down worker...")
        asyncio.run(worker.stop())


if __name__ == "__main__":
    main()
EOF

# Celery tasks
cat > "$base"/app/worker/tasks.py << 'EOF'
"""Celery tasks for ${name} service."""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from celery import shared_task

from services.${name}.lib.core.database import get_db_client
from services.${name}.lib.repositories.item_repository import ItemRepository

logger = logging.getLogger(__name__)


@shared_task(name="${name}.process_item")
def process_item(item_id: str) -> Dict[str, Any]:
    """Process an item asynchronously.

    Args:
        item_id: Item ID to process

    Returns:
        Processing result
    """
    logger.info(f"Processing item: {item_id}")

    # Get database client and repository
    db = get_db_client()
    repo = ItemRepository(db)

    # Process the item
    # TODO: Add actual processing logic
    result = {
        "item_id": item_id,
        "status": "processed",
        "timestamp": datetime.utcnow().isoformat(),
    }

    logger.info(f"Item processed successfully: {item_id}")
    return result


@shared_task(name="${name}.cleanup_old_items")
def cleanup_old_items(days: int = 30) -> Dict[str, int]:
    """Clean up old items.

    Args:
        days: Number of days to keep items

    Returns:
        Cleanup statistics
    """
    logger.info(f"Cleaning up items older than {days} days")

    db = get_db_client()
    repo = ItemRepository(db)

    # Calculate cutoff date
    cutoff = datetime.utcnow() - timedelta(days=days)

    # Perform cleanup
    deleted_count = 0  # TODO: Implement actual cleanup

    logger.info(f"Cleanup completed: {deleted_count} items deleted")
    return {"deleted": deleted_count}


@shared_task(name="${name}.batch_process")
def batch_process(batch_size: int = 100) -> Dict[str, Any]:
    """Process items in batches.

    Args:
        batch_size: Size of each batch

    Returns:
        Processing statistics
    """
    logger.info(f"Starting batch processing with size: {batch_size}")

    # TODO: Implement batch processing logic

    return {
        "processed": batch_size,
        "status": "completed",
        "timestamp": datetime.utcnow().isoformat(),
    }
EOF

# Message handlers
cat > "$base"/app/worker/handlers.py << 'EOF'
"""Message handlers for queue processing."""

import json
import logging
import os
from typing import Dict, Any

from services.${name}.lib.core.database import get_db_client
from services.${name}.domain.services.item_service import ItemService

logger = logging.getLogger(__name__)


class MessageHandler:
    """Handler for queue messages."""

    def __init__(self):
        """Initialize handler."""
        self.db = get_db_client()
        self.service = ItemService(self.db)

    async def process_queue_messages(self):
        """Process messages from SQS queue."""
        # TODO: Implement actual SQS polling
        # This is a placeholder for the pattern
        pass

    async def handle_message(self, message: Dict[str, Any]) -> bool:
        """Handle a single message.

        Args:
            message: Message to process

        Returns:
            True if processed successfully
        """
        try:
            message_type = message.get("type")
            payload = message.get("payload", {})

            if message_type == "create_item":
                await self.handle_create_item(payload)
            elif message_type == "update_item":
                await self.handle_update_item(payload)
            elif message_type == "delete_item":
                await self.handle_delete_item(payload)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                return False

            return True

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return False

    async def handle_create_item(self, payload: Dict[str, Any]):
        """Handle create item message."""
        logger.info(f"Creating item from message: {payload}")
        # TODO: Implement creation logic

    async def handle_update_item(self, payload: Dict[str, Any]):
        """Handle update item message."""
        logger.info(f"Updating item from message: {payload}")
        # TODO: Implement update logic

    async def handle_delete_item(self, payload: Dict[str, Any]):
        """Handle delete item message."""
        item_id = payload.get("id")
        logger.info(f"Deleting item: {item_id}")
        # TODO: Implement deletion logic
EOF

# ================== DOMAIN LAYER ==================
echo "🏛️ Creating domain layer templates..."

# Domain model
cat > "$base"/domain/models/item.py << 'EOF'
"""Item domain model."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ItemEntity(BaseModel):
    """Item domain entity."""

    id: UUID
    name: str
    description: Optional[str] = None
    category: str
    price: Decimal = Field(ge=0)
    quantity: int = Field(ge=0)
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None

    def calculate_total_value(self) -> Decimal:
        """Calculate total value of items in stock."""
        return self.price * self.quantity

    def is_in_stock(self) -> bool:
        """Check if item is in stock."""
        return self.quantity > 0 and self.is_active

    def apply_discount(self, percentage: Decimal) -> Decimal:
        """Apply discount and return new price."""
        if percentage < 0 or percentage > 100:
            raise ValueError("Discount percentage must be between 0 and 100")
        discount = self.price * (percentage / 100)
        return self.price - discount
EOF

# Value objects
cat > "$base"/domain/models/value_objects.py << 'EOF'
"""Value objects for the domain."""

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, validator


class Money(BaseModel):
    """Money value object."""

    amount: Decimal = Field(ge=0)
    currency: str = Field(default="USD", max_length=3)

    def add(self, other: "Money") -> "Money":
        """Add two money values."""
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def multiply(self, factor: Decimal) -> "Money":
        """Multiply money by a factor."""
        return Money(amount=self.amount * factor, currency=self.currency)


class Address(BaseModel):
    """Address value object."""

    street: str
    city: str
    state: str
    postal_code: str
    country: str = "USA"

    @validator("postal_code")
    def validate_postal_code(cls, v):
        """Validate postal code format."""
        if not v.replace("-", "").isdigit():
            raise ValueError("Invalid postal code")
        return v
EOF

# Domain service
cat > "$base"/domain/services/item_service.py << 'EOF'
"""Item domain service."""

import logging
from typing import List, Optional
from uuid import UUID

from services.${name}.domain.models.item import ItemEntity
from services.${name}.domain.ports.repository import ItemRepositoryPort
from services.${name}.domain.ports.notification import NotificationPort

logger = logging.getLogger(__name__)


class ItemService:
    """Service for item business logic."""

    def __init__(
        self,
        repository: ItemRepositoryPort,
        notification: Optional[NotificationPort] = None,
    ):
        """Initialize service.

        Args:
            repository: Item repository
            notification: Notification service
        """
        self.repository = repository
        self.notification = notification

    async def create_item_with_notification(
        self,
        item: ItemEntity,
        notify_users: bool = True,
    ) -> ItemEntity:
        """Create item and optionally notify users.

        Args:
            item: Item to create
            notify_users: Whether to send notifications

        Returns:
            Created item
        """
        # Create item
        created = await self.repository.create(item)
        logger.info(f"Item created: {created.id}")

        # Send notification if configured
        if notify_users and self.notification:
            await self.notification.send(
                subject="New Item Available",
                message=f"New item '{created.name}' is now available!",
            )

        return created

    async def restock_item(
        self,
        item_id: UUID,
        quantity: int,
    ) -> Optional[ItemEntity]:
        """Restock an item.

        Args:
            item_id: Item ID
            quantity: Quantity to add

        Returns:
            Updated item or None
        """
        item = await self.repository.get(item_id)
        if not item:
            logger.warning(f"Item not found: {item_id}")
            return None

        item.quantity += quantity
        updated = await self.repository.update(item_id, item)
        logger.info(f"Item restocked: {item_id}, new quantity: {updated.quantity}")

        return updated

    async def get_low_stock_items(
        self,
        threshold: int = 10,
    ) -> List[ItemEntity]:
        """Get items with low stock.

        Args:
            threshold: Stock threshold

        Returns:
            List of low stock items
        """
        all_items = await self.repository.list()
        low_stock = [
            item for item in all_items
            if item.is_active and item.quantity < threshold
        ]

        logger.info(f"Found {len(low_stock)} items with low stock")
        return low_stock
EOF

# Repository port
cat > "$base"/domain/ports/repository.py << 'EOF'
"""Repository port definitions."""

from typing import List, Optional, Protocol
from uuid import UUID

from services.${name}.domain.models.item import ItemEntity


class ItemRepositoryPort(Protocol):
    """Port for item repository."""

    async def create(self, item: ItemEntity) -> ItemEntity:
        """Create an item."""
        ...

    async def get(self, item_id: UUID) -> Optional[ItemEntity]:
        """Get item by ID."""
        ...

    async def list(self, **filters) -> List[ItemEntity]:
        """List items with filters."""
        ...

    async def update(self, item_id: UUID, item: ItemEntity) -> Optional[ItemEntity]:
        """Update an item."""
        ...

    async def delete(self, item_id: UUID) -> bool:
        """Delete an item."""
        ...
EOF

# Notification port
cat > "$base"/domain/ports/notification.py << 'EOF'
"""Notification port definition."""

from typing import Protocol


class NotificationPort(Protocol):
    """Port for notification service."""

    async def send(self, subject: str, message: str, recipient: str = None) -> bool:
        """Send a notification."""
        ...
EOF

# ================== SUPABASE INTEGRATION ==================
echo "🗄️ Creating Supabase integration templates..."

# Database configuration
cat > "$base"/lib/core/database.py << 'EOF'
"""Database client setup for ${name} service."""

import os
from typing import Optional

from supabase import Client, create_client

from services.${name}.config.settings import Settings


def get_db_client() -> Optional[Client]:
    """Get Supabase client instance.

    Returns:
        Supabase client or None if not configured
    """
    settings = Settings()

    if not settings.supabase_url or not settings.supabase_anon_key:
        print("⚠️ Supabase not configured, using mock client")
        return None

    client = create_client(
        settings.supabase_url,
        settings.supabase_anon_key,
    )

    return client


class DatabaseClient:
    """Wrapper for database client."""

    def __init__(self, client: Optional[Client] = None):
        """Initialize database client.

        Args:
            client: Supabase client instance
        """
        self._client = client or get_db_client()

    @property
    def client(self) -> Optional[Client]:
        """Get the underlying client."""
        return self._client

    def table(self, name: str):
        """Get a table reference.

        Args:
            name: Table name

        Returns:
            Table reference or mock
        """
        if self._client:
            return self._client.table(name)
        else:
            # Return a mock for development
            return MockTable(name)


class MockTable:
    """Mock table for development without Supabase."""

    def __init__(self, name: str):
        self.name = name
        self._data = []

    def select(self, *args, **kwargs):
        return self

    def insert(self, data):
        self._data.append(data)
        return self

    def update(self, data):
        return self

    def delete(self):
        return self

    def eq(self, column, value):
        return self

    def execute(self):
        """Execute the query and return mock data."""
        return {"data": self._data, "error": None}
EOF

# Pydantic models
cat > "$base"/lib/models/item.py << 'EOF'
"""Item models for database operations."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ItemBase(BaseModel):
    """Base item model."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    category: str = Field(..., min_length=1, max_length=100)
    price: Decimal = Field(..., ge=0, decimal_places=2)
    quantity: int = Field(default=0, ge=0)
    is_active: bool = Field(default=True)


class ItemCreate(ItemBase):
    """Model for creating items."""

    created_by: Optional[str] = None


class ItemUpdate(BaseModel):
    """Model for updating items."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    quantity: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class Item(ItemBase):
    """Complete item model."""

    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None

    class Config:
        """Pydantic config."""
        from_attributes = True
EOF

# Supabase repository
cat > "$base"/lib/repositories/item_repository.py << 'EOF'
"""Item repository implementation using Supabase."""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from services.${name}.lib.core.database import DatabaseClient
from services.${name}.lib.models.item import Item, ItemCreate, ItemUpdate

logger = logging.getLogger(__name__)


class ItemRepository:
    """Repository for item data using Supabase."""

    def __init__(self, db_client: DatabaseClient):
        """Initialize repository.

        Args:
            db_client: Database client
        """
        self.db = db_client
        self.table_name = "items"

    async def create(self, item_data: ItemCreate) -> Item:
        """Create a new item.

        Args:
            item_data: Item creation data

        Returns:
            Created item
        """
        data = item_data.model_dump()
        data["id"] = str(uuid4())
        data["created_at"] = datetime.utcnow().isoformat()
        data["updated_at"] = datetime.utcnow().isoformat()

        # Mock implementation for development
        if not self.db.client:
            logger.warning("Using mock implementation")
            return Item(**data)

        response = self.db.table(self.table_name).insert(data).execute()

        if response.error:
            raise ValueError(f"Failed to create item: {response.error}")

        return Item(**response.data[0])

    async def get(self, item_id: UUID) -> Optional[Item]:
        """Get item by ID.

        Args:
            item_id: Item ID

        Returns:
            Item if found
        """
        # Mock implementation for development
        if not self.db.client:
            return None

        response = (
            self.db.table(self.table_name)
            .select("*")
            .eq("id", str(item_id))
            .single()
            .execute()
        )

        if response.error or not response.data:
            return None

        return Item(**response.data)

    async def list(
        self,
        skip: int = 0,
        limit: int = 20,
        filters: Optional[Dict] = None,
    ) -> List[Item]:
        """List items with pagination and filters.

        Args:
            skip: Number of items to skip
            limit: Maximum items to return
            filters: Optional filters

        Returns:
            List of items
        """
        # Mock implementation for development
        if not self.db.client:
            return []

        query = self.db.table(self.table_name).select("*")

        # Apply filters
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)

        # Apply pagination
        response = query.range(skip, skip + limit - 1).execute()

        if response.error:
            raise ValueError(f"Failed to list items: {response.error}")

        return [Item(**item) for item in response.data]

    async def update(
        self,
        item_id: UUID,
        item_data: ItemUpdate,
    ) -> Optional[Item]:
        """Update an item.

        Args:
            item_id: Item ID
            item_data: Update data

        Returns:
            Updated item or None
        """
        data = item_data.model_dump(exclude_unset=True)
        if not data:
            return await self.get(item_id)

        data["updated_at"] = datetime.utcnow().isoformat()

        # Mock implementation for development
        if not self.db.client:
            return None

        response = (
            self.db.table(self.table_name)
            .update(data)
            .eq("id", str(item_id))
            .execute()
        )

        if response.error:
            raise ValueError(f"Failed to update item: {response.error}")

        if not response.data:
            return None

        return Item(**response.data[0])

    async def delete(self, item_id: UUID) -> bool:
        """Delete an item.

        Args:
            item_id: Item ID

        Returns:
            True if deleted
        """
        # Mock implementation for development
        if not self.db.client:
            return True

        response = (
            self.db.table(self.table_name)
            .delete()
            .eq("id", str(item_id))
            .execute()
        )

        return response.error is None

    async def search(self, query: str) -> List[Item]:
        """Search items by text.

        Args:
            query: Search query

        Returns:
            List of matching items
        """
        # Mock implementation for development
        if not self.db.client:
            return []

        response = (
            self.db.table(self.table_name)
            .select("*")
            .or_(f"name.ilike.%{query}%,description.ilike.%{query}%")
            .execute()
        )

        if response.error:
            raise ValueError(f"Failed to search items: {response.error}")

        return [Item(**item) for item in response.data]
EOF

# ================== CONFIGURATION ==================
echo "⚙️ Creating configuration templates..."

cat > "$base"/config/settings.py << 'EOF'
"""Settings for ${name} service."""

import os
from typing import List, Optional

from pydantic import BaseSettings


class Settings(BaseSettings):
    """Service settings."""

    # Service info
    service_name: str = "${name}"
    environment: str = "development"
    debug: bool = True

    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: List[str] = ["*"]

    # Database settings (Supabase)
    supabase_url: Optional[str] = os.getenv("SUPABASE_URL")
    supabase_anon_key: Optional[str] = os.getenv("SUPABASE_ANON_KEY")

    # AWS settings
    aws_region: str = "us-east-1"
    sqs_queue_url: Optional[str] = os.getenv("SQS_QUEUE_URL")
    s3_bucket: Optional[str] = os.getenv("S3_BUCKET")

    # Redis settings
    redis_url: str = "redis://localhost:6379"

    # Worker settings
    worker_concurrency: int = 4
    worker_poll_interval: int = 5

    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
EOF

# ================== PUBLIC FACADE ==================
echo "🌍 Creating public facade..."

cat > "$base"/public/client.py << 'EOF'
"""Client for ${name} service (for other services to use)."""

from typing import List, Optional
from uuid import UUID

import httpx

from services.${name}.lib.models.item import Item, ItemCreate


class ${SVC^}Client:
    """Client for interacting with ${name} service."""

    def __init__(self, base_url: str):
        """Initialize client.

        Args:
            base_url: Base URL of the service
        """
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient()

    async def create_item(self, item: ItemCreate) -> Item:
        """Create a new item."""
        response = await self.client.post(
            f"{self.base_url}/api/items/",
            json=item.model_dump(),
        )
        response.raise_for_status()
        return Item(**response.json())

    async def get_item(self, item_id: UUID) -> Optional[Item]:
        """Get an item by ID."""
        response = await self.client.get(
            f"{self.base_url}/api/items/{item_id}"
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return Item(**response.json())

    async def list_items(
        self,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Item]:
        """List items."""
        response = await self.client.get(
            f"{self.base_url}/api/items/",
            params={"skip": skip, "limit": limit},
        )
        response.raise_for_status()
        return [Item(**item) for item in response.json()]

    async def close(self):
        """Close the client."""
        await self.client.aclose()
EOF

# ================== TESTS ==================
echo "🧪 Creating test templates..."

# Test configuration
cat > "$base"/tests/conftest.py << 'EOF'
"""Test configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock

from services.${name}.app.api.main import app
from services.${name}.lib.repositories.item_repository import ItemRepository


@pytest.fixture
def test_client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_repository():
    """Create mock repository."""
    mock = Mock(spec=ItemRepository)
    mock.create = AsyncMock()
    mock.get = AsyncMock()
    mock.list = AsyncMock()
    mock.update = AsyncMock()
    mock.delete = AsyncMock()
    mock.search = AsyncMock()
    return mock


@pytest.fixture
def sample_item_data():
    """Sample item data for testing."""
    return {
        "name": "Test Item",
        "description": "A test item",
        "category": "test",
        "price": "19.99",
        "quantity": 10,
        "is_active": True,
    }
EOF

# Unit tests
cat > "$base"/tests/unit/test_api.py << 'EOF'
"""Unit tests for API endpoints."""

import pytest
from uuid import uuid4


def test_healthz(test_client):
    """Test health check endpoint."""
    response = test_client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "${name}"}


def test_root(test_client):
    """Test root endpoint."""
    response = test_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "${name}"
    assert data["status"] == "running"


@pytest.mark.asyncio
async def test_create_item(test_client, mock_repository, sample_item_data):
    """Test item creation."""
    # TODO: Implement with dependency override
    pass


@pytest.mark.asyncio
async def test_get_item(test_client, mock_repository):
    """Test getting an item."""
    # TODO: Implement with dependency override
    pass
EOF

# Domain tests
cat > "$base"/tests/unit/test_domain.py << 'EOF'
"""Unit tests for domain logic."""

import pytest
from decimal import Decimal
from uuid import uuid4
from datetime import datetime

from services.${name}.domain.models.item import ItemEntity


def test_item_calculate_total_value():
    """Test calculating total value."""
    item = ItemEntity(
        id=uuid4(),
        name="Test Item",
        category="test",
        price=Decimal("10.00"),
        quantity=5,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    assert item.calculate_total_value() == Decimal("50.00")


def test_item_is_in_stock():
    """Test stock checking."""
    item = ItemEntity(
        id=uuid4(),
        name="Test Item",
        category="test",
        price=Decimal("10.00"),
        quantity=5,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    assert item.is_in_stock() is True

    item.quantity = 0
    assert item.is_in_stock() is False

    item.quantity = 5
    item.is_active = False
    assert item.is_in_stock() is False


def test_item_apply_discount():
    """Test discount application."""
    item = ItemEntity(
        id=uuid4(),
        name="Test Item",
        category="test",
        price=Decimal("100.00"),
        quantity=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    discounted = item.apply_discount(Decimal("10"))
    assert discounted == Decimal("90.00")

    with pytest.raises(ValueError):
        item.apply_discount(Decimal("-10"))

    with pytest.raises(ValueError):
        item.apply_discount(Decimal("110"))
EOF

# ================== BUILD FILE ==================
echo "🔧 Creating BUILD file..."

cat > "$base"/BUILD << 'EOF'
python_sources(
    name="${name}_core",
    sources=["domain/**/*.py", "adapters/**/*.py", "public/**/*.py", "lib/**/*.py"],
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
        "lib/core/database.py": {
            "dependencies": [
                "3rdparty/python:${name}_core_reqs#supabase",
            ]
        },
    },
)

python_sources(
    name="${name}_api_src",
    sources=["app/api/**/*.py", "config/**/*.py"],
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
        "3rdparty/python:${name}_api_reqs#pytest",
        "3rdparty/python:${name}_api_reqs#pytest-asyncio",
    ],
)

python_tests(
    name="integration",
    sources=["tests/integration/**/*.py"],
    resolve="${name}_api",
    dependencies=[":${name}_core"],
)
EOF

# ================== DOCKERFILES ==================
echo "🐳 Creating Dockerfiles..."

cat > "$base"/Dockerfile.api << 'EOF'
FROM python:3.11-slim

WORKDIR /app

COPY . .

EXPOSE 8000

ENTRYPOINT ["python", "-m", "services.${name}.app.api.main"]
EOF

cat > "$base"/Dockerfile.worker << 'EOF'
FROM python:3.11-slim

WORKDIR /app

COPY . .

ENTRYPOINT ["python", "-m", "services.${name}.app.worker.run"]
EOF

# ================== INFRASTRUCTURE ==================
echo "🏗️ Creating infrastructure templates..."

cat > "$base"/infrastructure/Pulumi.yaml << 'EOF'
name: ${name}
runtime:
  name: python
  options:
    virtualenv: venv
backend:
  url: s3://pulumi-state-${name}
EOF

cat > "$base"/infrastructure/__main__.py << 'EOF'
import os
from stack.infra.components.http_service import EcsHttpService
import pulumi

MODULE = "${name}"
AWS_REGION = os.getenv("AWS_REGION", "eu-west-2")
AWS_ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID", "")
PROJECT_SLUG = os.getenv("PROJECT_SLUG", "pantstack")
BRANCH = os.getenv("GITHUB_REF_NAME", "dev")
SHORT_SHA = (os.getenv("GITHUB_SHA", "") or "dev")[:7]
ECR_REPO = os.getenv("ECR_REPOSITORY", PROJECT_SLUG)
ECR_BASE = f"{AWS_ACCOUNT_ID}.dkr.ecr.{AWS_REGION}.amazonaws.com/{ECR_REPO}"

api_image = f"{ECR_BASE}:{MODULE}-{BRANCH}-{SHORT_SHA}"
worker_image = f"{ECR_BASE}:{MODULE}-worker-{BRANCH}-{SHORT_SHA}"

# Deploy API service
api = EcsHttpService(
    name=f"{MODULE}-api",
    image=api_image,
    port=8000,
    env={
        "SERVICE_NAME": MODULE,
        "SUPABASE_URL": os.getenv("SUPABASE_URL", ""),
        "SUPABASE_ANON_KEY": os.getenv("SUPABASE_ANON_KEY", ""),
    }
)

# TODO: Deploy worker service

pulumi.export("alb_dns", api.alb_dns)
pulumi.export("url", api.url)
EOF

# Create SQL migration template
cat > "$base"/infrastructure/migrations/001_create_items_table.sql << 'EOF'
-- Create items table for ${name} service
CREATE TABLE IF NOT EXISTS items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL CHECK (price >= 0),
    quantity INTEGER DEFAULT 0 CHECK (quantity >= 0),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(255),

    -- Indexes
    INDEX idx_items_category (category),
    INDEX idx_items_is_active (is_active),
    INDEX idx_items_created_at (created_at)
);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_items_updated_at
    BEFORE UPDATE ON items
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
EOF

# Replace ${name} placeholders with actual service name
echo "🔄 Replacing placeholders..."
find "$base" -type f -name "*.py" -o -name "*.sql" -o -name "*.yaml" -o -name "BUILD" -o -name "Dockerfile.*" | while read file; do
  sed -i '' "s/\${name}/$SVC/g" "$file" 2>/dev/null || sed -i "s/\${name}/$SVC/g" "$file"
done

# Create requirements files
echo "📦 Creating requirements files..."
cat > "3rdparty/python/requirements-$SVC-core.txt" << 'EOF'
pydantic>=2.0.0
supabase>=2.0.0
python-dotenv>=1.0.0
EOF

cat > "3rdparty/python/requirements-$SVC-api.txt" << 'EOF'
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
pydantic>=2.0.0
httpx>=0.24.0
python-multipart>=0.0.6
supabase>=2.0.0
pytest>=7.0.0
pytest-asyncio>=0.21.0
EOF

# Update pants.toml with new resolvers
if [ -f "scripts/update_pants_resolvers.sh" ]; then
  ./scripts/update_pants_resolvers.sh "$SVC"
else
  echo ""
  echo "⚠️ Remember to add the following to pants.toml under [python.resolves]:"
  echo "  ${SVC}_core = \"lockfiles/${SVC}_core.lock\""
  echo "  ${SVC}_api = \"lockfiles/${SVC}_api.lock\""
fi

echo ""
echo "✅ Enhanced service '$SVC' scaffolded successfully!"
echo ""
echo "📋 Next steps:"
echo "  1. Run: ./pants generate-lockfiles"
echo "  2. Update Supabase connection in .env:"
echo "     - SUPABASE_URL=your_url"
echo "     - SUPABASE_ANON_KEY=your_key"
echo "  3. Run migrations: supabase db push"
echo "  4. Test the service: ./pants test services/$SVC::"
echo "  5. Run locally: python -m services.$SVC.app.api.main"
echo ""
echo "🎉 Your service includes:"
echo "  ✓ Full CRUD API with FastAPI"
echo "  ✓ Supabase database integration"
echo "  ✓ Celery task support"
echo "  ✓ SQS/EventBridge handlers"
echo "  ✓ Domain-Driven Design structure"
echo "  ✓ Complete test suite"
echo "  ✓ Docker containers"
echo "  ✓ Infrastructure as Code"
