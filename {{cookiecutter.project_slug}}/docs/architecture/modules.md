# Module Structure

Each service module in Pantstack follows a consistent structure designed for independence, testability, and clear boundaries.

## Module Layout

```
modules/{service}/
├── BUILD                    # Pants build configuration
├── README.md               # Module documentation
├── backend/                # Service implementation
│   ├── BUILD              # Backend build rules
│   ├── api/               # FastAPI application
│   │   ├── __init__.py
│   │   ├── main.py        # FastAPI app entry
│   │   └── routes/        # API endpoints
│   ├── service/           # Business logic
│   │   ├── __init__.py
│   │   └── core.py        # Core service logic
│   ├── worker/            # Async workers (optional)
│   │   ├── __init__.py
│   │   └── tasks.py       # Background tasks
│   ├── schemas/           # Data models
│   │   ├── __init__.py
│   │   └── models.py      # Pydantic models
│   ├── public/            # Public facade
│   │   ├── __init__.py
│   │   └── interface.py   # Public API
│   └── tests/             # Unit tests
│       ├── __init__.py
│       └── test_*.py      # Test files
└── infrastructure/        # Pulumi IaC
    ├── BUILD             # Infra build rules
    ├── __main__.py       # Pulumi program
    ├── Pulumi.yaml       # Pulumi project
    └── Pulumi.*.yaml     # Stack configs
```

## Key Components

### BUILD Files
Define Pants targets and dependencies:
- Python resolves for isolation
- Dependencies on other modules (via public facades only)
- Test configurations
- Docker image definitions

### Backend Directory

#### API Layer (`api/`)
- FastAPI application setup
- Route definitions
- Middleware configuration
- OpenAPI documentation

#### Service Layer (`service/`)
- Business logic implementation
- Domain models
- Service orchestration
- External integrations

#### Worker Layer (`worker/`)
- Asynchronous task processing
- SQS message handlers
- Scheduled jobs
- Background operations

#### Schemas (`schemas/`)
- Pydantic models for validation
- Request/response DTOs
- Domain entities
- Configuration models

#### Public Facade (`public/`)
- Stable interface for other modules
- Exported types and functions
- Service contracts
- Versioned APIs

### Infrastructure Directory
- Pulumi programs defining AWS resources
- Per-environment configurations
- Resource outputs for cross-stack references
- IAM policies and security groups

## Module Dependencies

### Allowed Dependencies
- Stack libraries (`stack/libs/*`)
- Other module public facades (`modules/*/backend/public`)
- Third-party packages (via requirements files)

### Prohibited Dependencies
- Direct imports from other module internals
- Cross-module backend imports (except public)
- Circular dependencies between modules

## Creating a New Module

```bash
# Create module structure
make new-module M=myservice

# Or create with PR
make gh-new-module-pr M=myservice
```

This scaffolds:
- Complete directory structure
- BUILD files with proper resolves
- Basic FastAPI application
- Pulumi infrastructure template
- Test setup

## Module Resolves

Each module has separate Python resolves:
- `{service}_core`: Core business logic
- `{service}_api`: API layer with FastAPI
- `{service}_test`: Test dependencies

Example from `pants.toml`:
```toml
[python.resolves]
api_core = "3rdparty/python/requirements-api-core.txt"
api_api = "3rdparty/python/requirements-api-api.txt"
admin_core = "3rdparty/python/requirements-admin-core.txt"
```

## Best Practices

1. **Keep modules focused**: Single responsibility principle
2. **Use public facades**: Never import from other module internals
3. **Test in isolation**: Each module should have comprehensive tests
4. **Document interfaces**: Clear documentation in public facades
5. **Version carefully**: Breaking changes to public APIs affect consumers
6. **Separate concerns**: API, service, and worker layers have distinct roles
