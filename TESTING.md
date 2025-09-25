# Testing Guidelines

## Philosophy

Focus on testing **business logic** and **service contracts**, not infrastructure details or boilerplate code. Tests should verify that your services work correctly, not that Docker or AWS work correctly.

## Test Organization

### Service-Level Testing
Each service owns its tests:
```
services/{service}/tests/
├── unit/                    # Pure business logic tests
├── integration/             # Service API integration tests
└── conftest.py             # Service-specific test fixtures
```

### Test Types

#### Unit Tests (`services/{service}/tests/unit/`)
- **Test**: Domain services, business logic, data transformations
- **Mock**: External dependencies (databases, APIs, queues)
- **Focus**: Pure functions, business rules, validation logic

```python
# Good: Testing business logic
def test_user_service_validates_email():
    user_service = UserService()
    with pytest.raises(ValidationError):
        user_service.create_user(email="invalid-email")

# Bad: Testing infrastructure
def test_dynamodb_connection():
    client = boto3.client('dynamodb')
    assert client.describe_table('users')
```

#### Integration Tests (`services/{service}/tests/integration/`)
- **Test**: API endpoints, service boundaries, adapter contracts
- **Use**: Real service instances, mocked external services
- **Focus**: HTTP APIs, service integration, end-to-end flows

```python
# Good: Testing API contract
async def test_auth_login_returns_token(client):
    response = await client.post('/login', json={
        'email': 'test@example.com',
        'password': 'valid_password'
    })
    assert response.status_code == 200
    assert 'access_token' in response.json()

# Bad: Testing infrastructure details
def test_postgres_connection_pool():
    pool = create_connection_pool()
    assert pool.maxconn == 20
```

## What NOT to Test

### ❌ Infrastructure Details
- Database connections, connection pools
- Docker container startup
- AWS service availability
- File system operations
- Environment variable parsing

### ❌ Third-Party Libraries
- FastAPI framework behavior
- Pydantic model validation (unless custom logic)
- SQLAlchemy ORM operations
- Redis client functionality

### ❌ Configuration and Setup
- BUILD files, pants configuration
- Docker compose files
- Environment setup
- Tool installation

### ❌ Generated Code
- `__init__.py` files (unless custom logic)
- Auto-generated models
- Migration files
- Template rendering

## What TO Test

### ✅ Business Logic
- Domain services and use cases
- Data validation and transformation
- Business rules and workflows
- Error handling and edge cases

### ✅ Service Contracts
- API endpoint behavior
- Request/response validation
- Authentication and authorization
- Cross-service communication

### ✅ Adapters (When They Contain Logic)
- Repository implementations with business logic
- External service integrations with transformation
- Queue handlers with processing logic

## Testing Patterns

### Use Dependency Injection for Testing
```python
class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

# Test with mock
def test_create_user():
    mock_repo = MagicMock()
    user_service = UserService(mock_repo)
    # Test business logic, not database
```

### Test Contracts, Not Implementation
```python
# Good: Test the contract
def test_get_user_returns_user_data():
    result = user_service.get_user("user-123")
    assert result["email"] == "test@example.com"
    assert "password" not in result  # Security requirement

# Bad: Test implementation details
def test_get_user_calls_repository_once():
    user_service.get_user("user-123")
    mock_repo.find_by_id.assert_called_once()
```

### Use Simple Test Doubles
```python
class FakeUserRepository:
    def __init__(self):
        self.users = {}

    def create(self, user_data):
        user_id = f"user-{len(self.users) + 1}"
        self.users[user_id] = user_data
        return user_id

# Prefer simple fakes over complex mocks
```

## Coverage Guidelines

### Target: 70-80% Coverage
- Focus on critical paths and business logic
- Don't aim for 100% coverage
- Coverage should guide testing, not drive it

### Service-Level Coverage
Each service reports its own coverage:
```bash
# Test single service with coverage
pants test services/auth/tests:: --test-use-coverage

# Generate coverage report
coverage report --include="services/auth/*"
```

### Coverage Exclusions
Automatically excluded (see `.coveragerc`):
- Infrastructure and configuration code
- Test files themselves
- Generated code and BUILD files
- Third-party integrations

## Running Tests

### Service Tests
```bash
# Run all tests for a service
pants test services/auth::

# Run only unit tests
pants test services/auth/tests/unit::

# Run with coverage
pants test services/auth:: --test-use-coverage
```

### Debugging Tests
```bash
# Run with verbose output
pants test services/auth:: --test-output=all

# Run specific test
pants test services/auth/tests/unit/test_services.py::test_create_user
```

## Test Organization Examples

### Good Service Test Structure
```
services/auth/tests/
├── unit/
│   ├── test_user_service.py      # User business logic
│   ├── test_auth_service.py      # Authentication logic
│   └── test_token_service.py     # Token generation/validation
├── integration/
│   └── test_auth_api.py          # HTTP API endpoints
└── conftest.py                   # Service-specific fixtures
```

### Example Unit Test
```python
"""Test user service business logic."""

from unittest.mock import MagicMock
import pytest
from services.auth.domain.services import UserService
from services.auth.domain.exceptions import ValidationError

class TestUserService:
    def test_create_user_validates_email(self):
        # Arrange
        mock_repo = MagicMock()
        user_service = UserService(mock_repo)

        # Act & Assert
        with pytest.raises(ValidationError, match="Invalid email"):
            user_service.create_user("invalid-email", "password")

    def test_create_user_hashes_password(self):
        # Arrange
        mock_repo = MagicMock()
        user_service = UserService(mock_repo)

        # Act
        user_service.create_user("test@example.com", "plain_password")

        # Assert
        saved_user = mock_repo.create.call_args[0][0]
        assert saved_user["password"] != "plain_password"
        assert len(saved_user["password"]) > 20  # Hashed
```

### Example Integration Test
```python
"""Test auth API integration."""

import pytest
from httpx import AsyncClient

@pytest.mark.integration
async def test_login_success(client: AsyncClient):
    # Arrange - create test user first
    await client.post("/register", json={
        "email": "test@example.com",
        "password": "SecurePass123!"
    })

    # Act
    response = await client.post("/login", json={
        "email": "test@example.com",
        "password": "SecurePass123!"
    })

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
```

## Anti-Patterns to Avoid

### Don't Test Everything
```python
# Bad: Testing obvious behavior
def test_user_init():
    user = User("test@example.com")
    assert user.email == "test@example.com"

# Bad: Testing framework behavior
def test_pydantic_validation():
    with pytest.raises(ValidationError):
        UserModel(email="invalid")
```

### Don't Mock What You Don't Own
```python
# Bad: Mocking third-party libraries
@patch('boto3.client')
def test_s3_upload(mock_boto):
    # Testing boto3, not your code

# Good: Mock your adapter
def test_file_upload():
    mock_storage = MagicMock()
    uploader = FileUploader(mock_storage)
    uploader.upload("file.txt", b"content")
    mock_storage.store.assert_called_once()
```

### Don't Test Implementation Details
```python
# Bad: Testing internal method calls
def test_service_calls_repo_twice():
    service.process_data()
    assert mock_repo.call_count == 2

# Good: Testing observable behavior
def test_service_returns_processed_data():
    result = service.process_data()
    assert result.status == "processed"
```

Remember: **Test behavior, not implementation. Test contracts, not details.**
