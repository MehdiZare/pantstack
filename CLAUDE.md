# CLAUDE.md - Developer Guide

This file provides practical guidance for working with the Pantstack monorepo.

## Quick Start

```bash
# 1. Install required tools
make setup

# 2. Bootstrap the project
make bootstrap

# 3. Run tests to verify setup
make test

# 4. Start local development
make dev-up
```

## Development Workflow

### Working with Services

#### Creating a New Service
```bash
# Generate service scaffold
make new-service S=orders

# This creates:
# - services/orders/ with DDD structure
# - Domain, adapters, and app layers
# - Infrastructure templates
# - BUILD files for Pants
# - Test scaffolding
```

#### Service Structure
```
services/{service}/
├── app/                 # Application layer
│   ├── api/            # HTTP endpoints
│   └── worker/         # Background workers
├── domain/             # Business logic
├── adapters/           # External integrations
├── lib/modules/        # Internal modules
├── public/             # Service contracts
├── infrastructure/     # Pulumi IaC
└── tests/              # Service tests
```

### Working with Modules

Modules are internal components within a service that group related functionality.

#### Creating a New Module

The CLI provides automated module generation with full DI integration:

```bash
# Generate module with DI container, repository, service, and routes
./scripts/new_module.sh orders inventory

# This creates:
# - Complete module structure with DI container
# - Repository with CRUD operations
# - Service with business logic
# - FastAPI routes with dependency injection
# - Pydantic schemas and error handling
# - Unit test scaffolding
```

Generated module structure:
```
services/{service}/lib/modules/{module}/
├── __init__.py           # Module exports
├── module.py             # Module interface + DI container
├── repository.py         # Data access layer
├── service.py            # Business logic layer
├── routes.py             # FastAPI routes with DI
├── schemas.py            # Pydantic models
├── tasks.py              # Celery tasks
├── handlers.py           # Event handlers
├── tests/
│   └── test_module.py    # Unit tests
└── BUILD                 # Pants build config
```

The generated module includes:
- **Dependency Injection Container**: Manages module dependencies
- **Repository Pattern**: CRUD operations with business logic separation
- **Service Layer**: Domain logic with validation
- **FastAPI Integration**: Routes with automatic DI wiring
- **Comprehensive Testing**: Unit tests for all components

#### Module Best Practices
- Keep modules focused on a single capability
- Modules within a service can directly call each other
- Use the service's `public/` facade for external communication
- Test modules in isolation when possible

#### Dependency Injection in Modules

Generated modules come with full DI container integration:

```python
# Module container automatically wires dependencies
class InventoryModuleContainer(containers.DeclarativeContainer):
    # Configuration
    config = providers.Singleton(InventoryConfig)

    # External dependencies (wired by service)
    db_client = providers.Dependency()
    redis_client = providers.Dependency()

    # Repository with dependency injection
    repository = providers.Singleton(
        InventoryRepository,
        db_client=db_client,
    )

    # Service with dependency injection
    service = providers.Factory(
        InventoryService,
        repository=repository,
        config=config,
    )
```

FastAPI routes use dependency injection:
```python
@router.post("/entities", response_model=InventoryEntity)
@inject
async def create_inventory_entity(
    entity_data: Dict[str, Any],
    service: InventoryService = Depends(Provide["inventory_service"]),
) -> InventoryEntity:
    return await service.create_entity(entity_data)
```

### Testing

#### Test Organization
```bash
# Unit tests - fast, isolated
services/{service}/tests/unit/

# Integration tests - service-level
services/{service}/tests/integration/

# Cross-service tests
tests/integration/

# Module tests
services/{service}/lib/modules/{module}/tests/
```

#### Running Tests
```bash
# All tests
make test

# Service tests
pants test services/auth::

# Module tests
pants test services/auth/lib/modules/users::

# With coverage
pants test --test-use-coverage services/auth::

# By tag
pants test --tag=unit ::
pants test --tag=integration ::
```

#### Writing Tests
```python
# Module unit test example
def test_module_initialization():
    module = UsersModule()
    assert module.name == "users"
    assert module.get_routes() is not None

# Service integration test example
async def test_service_workflow():
    # Test complete service workflow
    response = await client.post("/auth/login", json=data)
    assert response.status_code == 200
```

### Adding Dependencies

#### To a Service
1. Add to requirements file:
```bash
echo "requests==2.31.0" >> 3rdparty/python/requirements-{service}-core.txt
```

2. Regenerate lockfiles:
```bash
make locks
```

3. Import in your code:
```python
import requests
```

#### To a Module
Dependencies are managed at the service level. Modules inherit service dependencies.

### Local Development

#### Start Development Environment
```bash
# Start infrastructure (LocalStack, Redis, Supabase)
supabase start
make dev-up

# Run specific service
make dev-api-s S=auth
make dev-worker-s S=auth

# Stop everything
make dev-down
supabase stop
```

#### Environment Variables
```bash
# Local development
export LOCALSTACK=true
export SUPABASE_URL=http://localhost:54321
export ENV=local

# Test environment
export ENV=test
export AWS_PROFILE=test
```

### Deployment

#### Deploy Service to Environment
```bash
# Deploy to test
make stack-up S=auth ENV=test

# Preview changes
make stack-preview S=auth ENV=prod

# Deploy to production
make gha-deploy S=auth ENV=prod
```

#### Entry Point Optimization
Different entry points load different modules:

```python
# API entry point - loads all modules
from services.auth.lib import MODULES

# Lambda entry point - selective loading
from services.auth.lib.modules.tokens import TokenModule
modules = [TokenModule()]

# Worker entry point - task modules only
from services.auth.lib.modules.tasks import TaskModule
modules = [TaskModule()]
```

## Common Tasks

### Format and Lint Code
```bash
make fmt     # Format with Black and isort
make lint    # Run flake8 and mypy
```

### Update Dependencies
```bash
# Add new dependency
echo "package==version" >> 3rdparty/python/requirements-{service}-core.txt

# Update lockfiles
make locks

# Verify
pants peek 3rdparty/python::{service}_core
```

### Debug Pants Issues
```bash
# Check dependencies
pants dependencies services/auth::

# Check resolve
pants peek services/auth::

# Validate BUILD files
pants validate ::

# Clean cache
pants --no-pantsd clean-all
```

### Working with Pulumi
```bash
# Initialize stack
pulumi stack init {service}-{env}

# Deploy infrastructure
make stack-up S={service} ENV={env}

# Check outputs
make stack-outputs S={service} ENV={env}

# Destroy stack
make stack-down S={service} ENV={env}
```

## Troubleshooting

### Import Errors
1. Check dependency is in requirements file
2. Regenerate lockfiles: `make locks`
3. Check BUILD file dependencies
4. Clear Pants cache: `pants --no-pantsd clean-all`

### Test Failures
1. Check test isolation (no shared state)
2. Verify fixtures are properly scoped
3. Check environment variables
4. Run with verbose output: `pants test -ldebug ::`

### Module Discovery Issues
1. Verify module has proper `__init__.py`
2. Check module is registered in service
3. Verify module interface implementation
4. Check import paths are correct

### Deployment Issues
1. Check AWS credentials: `aws sts get-caller-identity`
2. Verify Pulumi stack exists: `pulumi stack ls`
3. Check environment variables in `.env`
4. Review CI/CD logs in GitHub Actions

## Best Practices

### Service Design
- Keep services focused on a single bounded context
- Use modules for internal organization
- Expose minimal public API
- Document service contracts

### Module Design
- One capability per module
- Clear module boundaries
- Minimal external dependencies
- Comprehensive module tests

### Testing Strategy
- Unit tests for business logic
- Integration tests for workflows
- Contract tests for APIs
- Load tests for performance

### Dependency Management
- Pin exact versions in requirements
- Regular dependency updates
- Security scanning with Dependabot
- Minimize transitive dependencies

## CI/CD Integration

### Pre-commit Hooks
```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### GitHub Actions
- Push to feature branch → Run tests
- PR to dev → Deploy preview stack
- Merge to dev → Deploy to test
- PR to main → Production preview
- Merge to main → Deploy to production

### Semantic Versioning
- `feat:` → Minor version bump
- `fix:` → Patch version bump
- `feat!:` → Major version bump
- Use PR labels to override

## Advanced Topics

### Custom Entry Points
Create specialized entry points for different deployment scenarios:

```python
# services/{service}/lambda_handler.py
from services.auth.lib.modules.tokens import TokenModule

def handler(event, context):
    module = TokenModule()
    return module.validate_token(event['token'])
```

### Service Mesh Integration
Services can be deployed with service mesh support:

```python
# infrastructure/__main__.py
service_mesh = ServiceMesh("auth-mesh",
    virtual_nodes=[...],
    virtual_services=[...]
)
```

### Event-Driven Architecture
Use the event backbone for async communication:

```python
# Publish events
from stack.events import EventPublisher
publisher = EventPublisher()
publisher.publish("user.created", data)

# Subscribe to events
from stack.events import EventSubscriber
subscriber = EventSubscriber()
subscriber.subscribe("user.created", handler)
```

## Recent Critical Fixes Applied

### Security & Infrastructure ✅
- **Fixed Auth Service DI**: Removed undefined variables, implemented proper dependency injection
- **Removed Hardcoded Secrets**: Eliminated hardcoded fallback secrets in Pulumi infrastructure
- **Fixed IAM Policies**: Replaced overly broad permissions with least-privilege access
- **Added SSL/HTTPS**: Implemented ACM certificates with automatic HTTP→HTTPS redirect
- **Enhanced Security Groups**: Separated ALB and ECS security groups with proper restrictions

### Monitoring & Operations ✅
- **Added CloudWatch Dashboard**: Comprehensive monitoring for ECS, ALB, and DynamoDB
- **Implemented Alerting**: CPU, error rate, and response time alarms
- **Enhanced CLI Tools**: Complete DI integration in service and module generation

### Build System ✅
- **Fixed Dependencies**: Added missing packages to auth_core resolve
- **Resolved Import Issues**: Fixed redis, supabase, celery, dependency-injector imports

### Known Remaining Issues
- Cross-resolve dependency issues with shared libraries (requires Pants config refactor)
- Some test configurations may need resolve adjustment

### Dependency Management
If you encounter import errors:
1. Add dependencies to correct requirements file (`requirements-{service}-core.txt`)
2. Run: `pants generate-lockfiles --resolve={service}_core`
3. For cross-resolve issues, see Pants documentation on parametrized targets

## Getting Help

- Check existing services for examples
- Review test files for usage patterns
- Consult README.md for architecture overview
- Submit issues to GitHub repository
