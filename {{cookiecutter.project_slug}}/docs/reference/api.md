# API Reference

Complete API reference for Pantstack services and modules.

## Service APIs

### Base Service Structure

All services follow a consistent API structure:

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="Service Name",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)
```

### Common Endpoints

#### Health Check
```http
GET /health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### Metrics
```http
GET /metrics
```

Response (Prometheus format):
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/health"} 1234
```

## API Module

### User Management

#### Create User
```http
POST /api/v1/users
Content-Type: application/json

{
  "email": "user@example.com",
  "name": "John Doe",
  "password": "secure_password"
}
```

Response:
```json
{
  "id": "usr_abc123",
  "email": "user@example.com",
  "name": "John Doe",
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### Get User
```http
GET /api/v1/users/{user_id}
Authorization: Bearer <token>
```

Response:
```json
{
  "id": "usr_abc123",
  "email": "user@example.com",
  "name": "John Doe",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

#### Update User
```http
PUT /api/v1/users/{user_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Jane Doe",
  "email": "jane@example.com"
}
```

#### Delete User
```http
DELETE /api/v1/users/{user_id}
Authorization: Bearer <token>
```

Response: `204 No Content`

### Authentication

#### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password"
}
```

Response:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### Refresh Token
```http
POST /api/v1/auth/refresh
Authorization: Bearer <refresh_token>
```

Response:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### Logout
```http
POST /api/v1/auth/logout
Authorization: Bearer <token>
```

Response: `204 No Content`

## Admin Module

### System Management

#### Get System Status
```http
GET /api/v1/admin/system/status
Authorization: Bearer <admin_token>
```

Response:
```json
{
  "services": [
    {
      "name": "api",
      "status": "running",
      "uptime": 86400,
      "memory_usage": "256MB",
      "cpu_usage": "10%"
    }
  ],
  "database": {
    "status": "connected",
    "latency_ms": 5
  },
  "cache": {
    "status": "connected",
    "hit_rate": 0.95
  }
}
```

#### Trigger Maintenance Mode
```http
POST /api/v1/admin/maintenance
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "enabled": true,
  "message": "System maintenance in progress"
}
```

## Data Models

### User Schema
```python
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    password: Optional[str] = None

class User(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
```

### Error Response
```python
class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    request_id: str
    timestamp: datetime
```

## Public Facades

### Service Client Interface

Each service exposes a public client for inter-service communication:

```python
# modules/api/backend/public/client.py
from typing import Optional, List
from ..schemas.models import User

class APIClient:
    """Client for interacting with the API service."""

    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url
        self.api_key = api_key

    async def get_user(self, user_id: str) -> Optional[User]:
        """Retrieve a user by ID."""
        # Implementation
        pass

    async def list_users(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[User]:
        """List users with pagination."""
        # Implementation
        pass

    async def verify_user(self, user_id: str, token: str) -> bool:
        """Verify user authentication."""
        # Implementation
        pass
```

### Using Service Clients

```python
# In another service
from modules.api.backend.public import APIClient

async def process_order(order_data: dict):
    api_client = APIClient(base_url="http://api-service:8000")

    # Verify user exists
    user = await api_client.get_user(order_data["user_id"])
    if not user:
        raise ValueError("User not found")

    # Process order...
```

## WebSocket APIs

### Real-time Updates

```python
from fastapi import WebSocket

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()

            # Process and respond
            response = process_message(data)
            await websocket.send_json(response)
    except WebSocketDisconnect:
        await manager.disconnect(client_id)
```

### Client Connection

```javascript
// JavaScript client
const ws = new WebSocket("ws://localhost:8000/ws/client123");

ws.onopen = () => {
    ws.send(JSON.stringify({type: "subscribe", channel: "updates"}));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log("Received:", data);
};
```

## GraphQL API (Optional)

### Schema Definition

```python
import strawberry
from typing import List

@strawberry.type
class User:
    id: str
    email: str
    name: str

@strawberry.type
class Query:
    @strawberry.field
    async def user(self, id: str) -> User:
        return await get_user(id)

    @strawberry.field
    async def users(self, limit: int = 10) -> List[User]:
        return await list_users(limit)

schema = strawberry.Schema(query=Query)
```

### GraphQL Endpoint

```python
from strawberry.fastapi import GraphQLRouter

graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")
```

## Error Handling

### Standard Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `AUTH_001` | Invalid credentials | 401 |
| `AUTH_002` | Token expired | 401 |
| `AUTH_003` | Insufficient permissions | 403 |
| `VAL_001` | Validation error | 400 |
| `VAL_002` | Missing required field | 400 |
| `RES_001` | Resource not found | 404 |
| `RES_002` | Resource already exists | 409 |
| `SYS_001` | Internal server error | 500 |
| `SYS_002` | Service unavailable | 503 |

### Error Handler

```python
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": f"HTTP_{exc.status_code}",
            "message": exc.detail,
            "request_id": request.headers.get("X-Request-ID"),
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

## Rate Limiting

### Configuration

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"]
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/v1/users")
@limiter.limit("10/minute")
async def list_users():
    # Implementation
    pass
```

## API Versioning

### URL Path Versioning

```python
# Version 1
v1_router = APIRouter(prefix="/api/v1")

@v1_router.get("/users")
async def get_users_v1():
    # V1 implementation
    pass

# Version 2
v2_router = APIRouter(prefix="/api/v2")

@v2_router.get("/users")
async def get_users_v2():
    # V2 implementation with new features
    pass

app.include_router(v1_router)
app.include_router(v2_router)
```

### Header-Based Versioning

```python
from fastapi import Header

@app.get("/api/users")
async def get_users(api_version: str = Header(default="v1")):
    if api_version == "v2":
        return get_users_v2_logic()
    return get_users_v1_logic()
```

## Testing APIs

### Unit Tests

```python
from fastapi.testclient import TestClient

def test_create_user():
    client = TestClient(app)
    response = client.post("/api/v1/users", json={
        "email": "test@example.com",
        "name": "Test User",
        "password": "password123"
    })
    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"
```

### Integration Tests

```python
import httpx
import pytest

@pytest.mark.asyncio
async def test_user_workflow():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # Create user
        create_resp = await client.post("/api/v1/users", json={...})
        user_id = create_resp.json()["id"]

        # Verify user
        get_resp = await client.get(f"/api/v1/users/{user_id}")
        assert get_resp.status_code == 200
```

## API Documentation

### OpenAPI/Swagger

Automatically generated at `/api/docs`:
- Interactive API documentation
- Try out endpoints directly
- View request/response schemas

### ReDoc

Alternative documentation at `/api/redoc`:
- Clean, responsive design
- Better for API reference
- Printable documentation

### Custom Documentation

```python
app = FastAPI(
    title="Pantstack API",
    description="Complete API for Pantstack services",
    version="1.0.0",
    terms_of_service="https://pantstack.example.com/terms",
    contact={
        "name": "API Support",
        "email": "api@pantstack.example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)
```
