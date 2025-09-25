# Module Development Guide

This guide covers the complete lifecycle of developing a service module in Pantstack.

## Creating a New Module

### Quick Start
```bash
# Create a new module with scaffolding
make new-module M=orders

# Or create with GitHub PR workflow
make gh-new-module-pr M=orders
```

### What Gets Created
```
modules/orders/
├── BUILD                    # Pants configuration
├── README.md               # Module documentation
├── backend/
│   ├── BUILD
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py         # FastAPI app
│   │   └── routes/
│   │       └── health.py
│   ├── service/
│   │   ├── __init__.py
│   │   └── core.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── models.py
│   ├── public/
│   │   ├── __init__.py
│   │   └── interface.py    # Public API
│   └── tests/
│       ├── __init__.py
│       └── test_main.py
└── infrastructure/
    ├── BUILD
    ├── __main__.py         # Pulumi program
    ├── Pulumi.yaml
    └── requirements.txt
```

## Module Configuration

### BUILD File Setup
```python
# modules/orders/BUILD
python_sources(
    name="lib",
    resolve="orders_core",
    dependencies=[
        "stack/libs/common",
        "modules/api/backend/public",  # Only public facades
    ],
)

pex_binary(
    name="api",
    entry_point="backend/api/main.py",
    resolve="orders_api",
)

docker_image(
    name="docker",
    dependencies=[":api"],
    repository="pantstack",
    tags=["orders-{version}"],
)
```

### Python Resolves
Each module has isolated dependency sets:
```toml
# pants.toml
[python.resolves]
orders_core = "3rdparty/python/requirements-orders-core.txt"
orders_api = "3rdparty/python/requirements-orders-api.txt"
orders_test = "3rdparty/python/requirements-orders-test.txt"
```

## Implementing the Service

### FastAPI Application
```python
# modules/orders/backend/api/main.py
from fastapi import FastAPI
from .routes import health, orders

app = FastAPI(
    title="Orders Service",
    version="1.0.0",
    docs_url="/api/docs",
)

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(orders.router, prefix="/api/v1/orders", tags=["orders"])

@app.on_event("startup")
async def startup_event():
    # Initialize connections, caches, etc.
    pass
```

### Service Layer
```python
# modules/orders/backend/service/orders_service.py
from typing import List, Optional
from ..schemas.models import Order, CreateOrderRequest

class OrdersService:
    async def create_order(self, request: CreateOrderRequest) -> Order:
        # Business logic
        order = Order(
            id=generate_id(),
            customer_id=request.customer_id,
            items=request.items,
            status="pending",
        )
        await self._save_order(order)
        return order

    async def get_order(self, order_id: str) -> Optional[Order]:
        return await self._fetch_order(order_id)
```

### API Routes
```python
# modules/orders/backend/api/routes/orders.py
from fastapi import APIRouter, HTTPException, Depends
from ...service.orders_service import OrdersService
from ...schemas.models import Order, CreateOrderRequest

router = APIRouter()

def get_service() -> OrdersService:
    return OrdersService()

@router.post("/", response_model=Order)
async def create_order(
    request: CreateOrderRequest,
    service: OrdersService = Depends(get_service)
) -> Order:
    return await service.create_order(request)

@router.get("/{order_id}", response_model=Order)
async def get_order(
    order_id: str,
    service: OrdersService = Depends(get_service)
) -> Order:
    order = await service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
```

## Public Facade Pattern

### Creating a Public Interface
```python
# modules/orders/backend/public/interface.py
"""Public interface for the Orders service.

This module exposes stable APIs for other services to use.
"""
from typing import Optional
from ..schemas.models import Order

class OrdersClient:
    """Client for interacting with the Orders service."""

    async def get_order(self, order_id: str) -> Optional[Order]:
        """Retrieve an order by ID."""
        # Implementation that other services can use
        pass

    async def check_order_exists(self, order_id: str) -> bool:
        """Check if an order exists."""
        order = await self.get_order(order_id)
        return order is not None
```

### Using from Another Module
```python
# modules/shipping/backend/service/shipping_service.py
from modules.orders.backend.public import OrdersClient

class ShippingService:
    def __init__(self):
        self.orders_client = OrdersClient()

    async def ship_order(self, order_id: str):
        if not await self.orders_client.check_order_exists(order_id):
            raise ValueError(f"Order {order_id} not found")
        # Shipping logic
```

## Testing

### Unit Tests
```python
# modules/orders/backend/tests/test_service.py
import pytest
from ..service.orders_service import OrdersService
from ..schemas.models import CreateOrderRequest

@pytest.mark.asyncio
async def test_create_order():
    service = OrdersService()
    request = CreateOrderRequest(
        customer_id="cust-123",
        items=[{"product_id": "prod-1", "quantity": 2}]
    )

    order = await service.create_order(request)

    assert order.customer_id == "cust-123"
    assert order.status == "pending"
    assert len(order.items) == 1
```

### Integration Tests
```python
# modules/orders/backend/tests/test_api.py
from fastapi.testclient import TestClient
from ..api.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_create_order():
    response = client.post("/api/v1/orders", json={
        "customer_id": "cust-123",
        "items": [{"product_id": "prod-1", "quantity": 2}]
    })
    assert response.status_code == 200
    assert "id" in response.json()
```

### Running Tests
```bash
# Run module tests
pants test modules/orders::

# Run with coverage
pants test --use-coverage modules/orders::

# Run specific test file
pants test modules/orders/backend/tests/test_service.py
```

## Dependencies

### Adding Dependencies
```bash
# Add to requirements file
echo "redis==5.0.0" >> 3rdparty/python/requirements-orders-core.txt

# Regenerate lockfiles
make locks

# Or just for this module
pants generate-lockfiles --resolve=orders_core
```

### Cross-Module Dependencies
```python
# modules/orders/BUILD
python_sources(
    dependencies=[
        # ✅ Allowed: Public facades
        "modules/inventory/backend/public",
        "modules/auth/backend/public",

        # ❌ Not allowed: Internal implementations
        # "modules/inventory/backend/service",

        # ✅ Allowed: Shared libraries
        "stack/libs/common",
        "stack/libs/database",
    ],
)
```

## Local Development

### Running Locally
```bash
# Install dependencies
cd modules/orders
pip install -r ../../3rdparty/python/requirements-orders-api.txt

# Run with hot reload
uvicorn backend.api.main:app --reload --port 8001

# Or use Docker
docker-compose up orders
```

### Environment Variables
```python
# modules/orders/backend/config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql://localhost/orders"
    redis_url: str = "redis://localhost"
    aws_region: str = "us-east-1"
    log_level: str = "INFO"

    class Config:
        env_prefix = "ORDERS_"
        env_file = ".env"

settings = Settings()
```

## Deployment

### Infrastructure Setup
```python
# modules/orders/infrastructure/__main__.py
import pulumi
import pulumi_aws as aws

# Create ECS service
service = aws.ecs.Service(
    "orders-service",
    cluster=cluster.arn,
    task_definition=task_def.arn,
    desired_count=2,
    launch_type="FARGATE",
    network_configuration={
        "subnets": private_subnet_ids,
        "security_groups": [service_sg.id],
    },
)

# Create ALB target group
target_group = aws.lb.TargetGroup(
    "orders-tg",
    port=8000,
    protocol="HTTP",
    vpc_id=vpc.id,
    target_type="ip",
    health_check={
        "path": "/health",
        "interval": 30,
    },
)
```

### Deploy Commands
```bash
# Deploy to test environment
make stack-up M=orders ENV=test

# Preview changes first
make stack-preview M=orders ENV=test

# Deploy to production
make stack-up M=orders ENV=prod
```

## Best Practices

### Code Organization
1. Keep business logic in service layer
2. Use schemas for validation
3. Expose minimal public API
4. Write comprehensive tests
5. Document public interfaces

### Performance
1. Use async/await for I/O operations
2. Implement caching where appropriate
3. Use connection pooling
4. Monitor resource usage
5. Set up auto-scaling

### Security
1. Validate all inputs
2. Use environment variables for secrets
3. Implement rate limiting
4. Add authentication/authorization
5. Log security events

### Monitoring
1. Add health check endpoints
2. Implement structured logging
3. Export metrics to CloudWatch
4. Set up alerts for errors
5. Use distributed tracing

## Troubleshooting

### Common Issues

#### Module Import Errors
```bash
# Check resolve configuration
pants peek modules/orders::

# Verify dependencies
pants dependencies modules/orders::

# Clear cache and rebuild
rm -rf ~/.cache/pants
pants test modules/orders::
```

#### Test Failures
```bash
# Run with debug output
pants test modules/orders:: -ldebug

# Run specific test
pants test modules/orders/backend/tests/test_service.py::test_create_order
```

#### Build Issues
```bash
# Check BUILD file syntax
pants validate modules/orders::

# Show build graph
pants dependencies --transitive modules/orders::
```
