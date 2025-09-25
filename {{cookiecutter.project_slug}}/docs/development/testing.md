# Testing Guide

Comprehensive testing is essential for maintaining code quality in the Pantstack monorepo. This guide covers testing strategies, tools, and best practices.

## Testing Philosophy

- **Test Pyramid**: Unit tests > Integration tests > E2E tests
- **Fast Feedback**: Tests should run quickly and provide clear results
- **Isolation**: Tests should not depend on external services unless necessary
- **Coverage**: Aim for 80%+ code coverage on critical paths

## Test Organization

### Directory Structure
```
modules/{service}/
└── backend/
    ├── tests/              # Test files
    │   ├── __init__.py
    │   ├── conftest.py    # Pytest fixtures
    │   ├── unit/          # Unit tests
    │   │   ├── test_service.py
    │   │   └── test_models.py
    │   ├── integration/   # Integration tests
    │   │   ├── test_api.py
    │   │   └── test_database.py
    │   └── e2e/          # End-to-end tests
    │       └── test_workflows.py
    └── testdata/         # Test fixtures and data
        └── sample_data.json
```

## Unit Testing

### Basic Test Structure
```python
# modules/api/backend/tests/unit/test_service.py
import pytest
from unittest.mock import Mock, patch
from ...service.user_service import UserService
from ...schemas.models import User, CreateUserRequest

class TestUserService:
    @pytest.fixture
    def service(self):
        return UserService()

    @pytest.fixture
    def mock_db(self):
        with patch('...service.user_service.database') as mock:
            yield mock

    def test_create_user(self, service, mock_db):
        # Arrange
        request = CreateUserRequest(
            email="test@example.com",
            name="Test User"
        )
        mock_db.save.return_value = True

        # Act
        user = service.create_user(request)

        # Assert
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        mock_db.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_get_user(self, service, mock_db):
        # Arrange
        mock_db.fetch.return_value = {"id": "123", "email": "test@example.com"}

        # Act
        user = await service.get_user("123")

        # Assert
        assert user.id == "123"
        assert user.email == "test@example.com"
```

### Testing with Fixtures
```python
# modules/api/backend/tests/conftest.py
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

@pytest.fixture(scope="session")
def db_engine():
    """Create a test database engine."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """Create a new database session for each test."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session) -> TestClient:
    """Create a test client with database session."""
    from ..api.main import app
    app.dependency_overrides[get_db] = lambda: db_session
    return TestClient(app)
```

## Integration Testing

### API Testing
```python
# modules/api/backend/tests/integration/test_api.py
import pytest
from fastapi.testclient import TestClient
from ...api.main import app

class TestAPIIntegration:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_user_workflow(self, client):
        # Create user
        create_response = client.post("/api/v1/users", json={
            "email": "test@example.com",
            "name": "Test User"
        })
        assert create_response.status_code == 201
        user_id = create_response.json()["id"]

        # Get user
        get_response = client.get(f"/api/v1/users/{user_id}")
        assert get_response.status_code == 200
        assert get_response.json()["email"] == "test@example.com"

        # Update user
        update_response = client.put(f"/api/v1/users/{user_id}", json={
            "name": "Updated Name"
        })
        assert update_response.status_code == 200
        assert update_response.json()["name"] == "Updated Name"

        # Delete user
        delete_response = client.delete(f"/api/v1/users/{user_id}")
        assert delete_response.status_code == 204

        # Verify deletion
        verify_response = client.get(f"/api/v1/users/{user_id}")
        assert verify_response.status_code == 404
```

### Database Testing
```python
# modules/api/backend/tests/integration/test_database.py
import pytest
from sqlalchemy.orm import Session
from ...database.models import User
from ...database.repository import UserRepository

class TestDatabaseIntegration:
    @pytest.fixture
    def repository(self, db_session: Session):
        return UserRepository(db_session)

    def test_user_crud(self, repository, db_session):
        # Create
        user = User(email="test@example.com", name="Test User")
        created = repository.create(user)
        assert created.id is not None

        # Read
        fetched = repository.get(created.id)
        assert fetched.email == "test@example.com"

        # Update
        fetched.name = "Updated Name"
        updated = repository.update(fetched)
        assert updated.name == "Updated Name"

        # Delete
        repository.delete(created.id)
        assert repository.get(created.id) is None
```

## End-to-End Testing

### Service Communication Tests
```python
# modules/api/backend/tests/e2e/test_service_integration.py
import pytest
import httpx
from unittest.mock import patch

class TestServiceIntegration:
    @pytest.mark.asyncio
    async def test_order_fulfillment_workflow(self):
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            # Create order
            order_response = await client.post("/api/v1/orders", json={
                "customer_id": "cust-123",
                "items": [{"product_id": "prod-1", "quantity": 2}]
            })
            order_id = order_response.json()["id"]

            # Process payment
            payment_response = await client.post("/api/v1/payments", json={
                "order_id": order_id,
                "amount": 99.99,
                "method": "credit_card"
            })
            assert payment_response.status_code == 200

            # Check order status
            status_response = await client.get(f"/api/v1/orders/{order_id}")
            assert status_response.json()["status"] == "paid"

            # Trigger shipping
            shipping_response = await client.post(f"/api/v1/orders/{order_id}/ship")
            assert shipping_response.status_code == 200
```

## Mocking and Patching

### External Service Mocking
```python
# modules/api/backend/tests/unit/test_external_service.py
import pytest
from unittest.mock import patch, Mock
import httpx

class TestExternalService:
    @patch('httpx.AsyncClient.get')
    async def test_fetch_external_data(self, mock_get):
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "value"}
        mock_get.return_value = mock_response

        # Act
        from ...service.external_service import fetch_data
        result = await fetch_data("https://api.example.com/data")

        # Assert
        assert result == {"data": "value"}
        mock_get.assert_called_with("https://api.example.com/data")
```

### AWS Service Mocking
```python
# modules/api/backend/tests/unit/test_aws_service.py
import pytest
from moto import mock_s3, mock_sqs
import boto3

class TestAWSIntegration:
    @mock_s3
    def test_s3_operations(self):
        # Create mock S3
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='test-bucket')

        # Test upload
        from ...service.storage_service import upload_file
        result = upload_file('test-bucket', 'test.txt', b'content')
        assert result is True

        # Verify
        objects = s3.list_objects(Bucket='test-bucket')
        assert len(objects.get('Contents', [])) == 1

    @mock_sqs
    def test_sqs_operations(self):
        # Create mock queue
        sqs = boto3.client('sqs', region_name='us-east-1')
        queue_url = sqs.create_queue(QueueName='test-queue')['QueueUrl']

        # Test message sending
        from ...service.queue_service import send_message
        result = send_message(queue_url, {"action": "process"})
        assert result is not None

        # Verify
        messages = sqs.receive_message(QueueUrl=queue_url)
        assert len(messages.get('Messages', [])) == 1
```

## Test Coverage

### Running with Coverage
```bash
# Run tests with coverage
pants test --use-coverage modules/api::

# Generate HTML report
pants test --use-coverage modules/api:: \
  --coverage-py-report=html:htmlcov

# View coverage report
open htmlcov/index.html
```

### Coverage Configuration
```ini
# .coveragerc
[run]
source = modules/
omit =
    */tests/*
    */test_*.py
    */__init__.py
    */conftest.py

[report]
precision = 2
show_missing = True
skip_covered = False

[html]
directory = htmlcov
```

## Performance Testing

### Load Testing with Locust
```python
# modules/api/backend/tests/performance/locustfile.py
from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def get_health(self):
        self.client.get("/health")

    @task(2)
    def get_user(self):
        user_id = "123"
        self.client.get(f"/api/v1/users/{user_id}")

    @task(1)
    def create_user(self):
        self.client.post("/api/v1/users", json={
            "email": f"test{self.environment.runner.user_count}@example.com",
            "name": "Load Test User"
        })
```

### Running Load Tests
```bash
# Start Locust
locust -f modules/api/backend/tests/performance/locustfile.py \
  --host=http://localhost:8000

# Or headless
locust -f modules/api/backend/tests/performance/locustfile.py \
  --host=http://localhost:8000 \
  --users=100 \
  --spawn-rate=10 \
  --time=60s \
  --headless
```

## Testing Commands

### Running Tests
```bash
# Run all tests
make test

# Run specific module tests
pants test modules/api::

# Run specific test file
pants test modules/api/backend/tests/test_service.py

# Run specific test
pants test modules/api/backend/tests/test_service.py::test_create_user

# Run with verbose output
pants test modules/api:: -v

# Run with debug output
pants test modules/api:: -ldebug
```

### Test Filtering
```bash
# Run only unit tests
pants test modules/api/backend/tests/unit::

# Run tests matching pattern
pants test modules/api:: -k "test_create"

# Run marked tests
pants test modules/api:: -m "slow"

# Exclude tests
pants test modules/api:: -m "not slow"
```

## Test Markers

### Using Pytest Markers
```python
# modules/api/backend/tests/test_service.py
import pytest

@pytest.mark.unit
def test_simple_calculation():
    assert 1 + 1 == 2

@pytest.mark.integration
@pytest.mark.slow
def test_database_operation():
    # Long-running test
    pass

@pytest.mark.skip(reason="Not implemented yet")
def test_future_feature():
    pass

@pytest.mark.skipif(
    not os.environ.get("AWS_ACCESS_KEY_ID"),
    reason="AWS credentials not available"
)
def test_aws_integration():
    pass
```

## CI Testing

### GitHub Actions Test Job
```yaml
# .github/workflows/ci.yml
test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'

    - name: Install Pants
      run: |
        curl -L -o pants https://pantsbuild.github.io/setup/pants
        chmod +x pants
        mv pants ~/.local/bin/

    - name: Run Tests
      run: |
        pants test ::

    - name: Upload Coverage
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.xml
```

## Best Practices

1. **Write tests first** (TDD) when possible
2. **Keep tests simple and focused** - one assertion per test ideally
3. **Use descriptive test names** that explain what is being tested
4. **Isolate tests** - no shared state between tests
5. **Mock external dependencies** to ensure fast, reliable tests
6. **Test edge cases** and error conditions
7. **Maintain test data** in version control
8. **Run tests locally** before pushing
9. **Keep test coverage high** but focus on quality over quantity
10. **Refactor tests** along with production code
