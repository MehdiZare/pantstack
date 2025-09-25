# Pantstack Architecture Plan

## Quick Start

```bash
# 1. Install required tools
make setup            # Interactive setup for all required tools
# Or individually:
make install-uv       # Fast Python package installer
make install-pants    # Build system
make install-pulumi   # Infrastructure as Code
make install-aws      # AWS CLI
make install-gh       # GitHub CLI
make check-tools      # Verify all tools are installed

# 2. Initialize configuration
cp .env.example .env  # Copy example environment file
chmod +x .localstack/init/ready.d/*.sh  # Fix LocalStack script permissions

# 3. Initialize and start Supabase
supabase init  # One-time setup
supabase start  # Starts PostgreSQL, Auth, Storage, Realtime

# 4. Start LocalStack and other services
docker compose up -d localstack redis

# 5. Verify services are running
# Check LocalStack resources
docker compose logs localstack | grep "initialization complete"
aws --endpoint-url=http://localhost:4566 dynamodb list-tables
aws --endpoint-url=http://localhost:4566 s3 ls

# Check Supabase
supabase status

# 6. Run API locally (two options)
# Option A: Via Docker
docker compose up -d api

# Option B: Directly with Python
python -m entry_points.api.run

# 7. Run Celery worker
docker compose up -d celery_worker

# 8. Run tests
pants test ::        # Run all tests with Pants
make test            # Or use Makefile wrapper
```

The system automatically:
- Detects LocalStack and configures all AWS endpoints
- Creates all required AWS resources via init scripts
- Connects to Supabase for database, auth, and storage
- Seeds test data
- Validates configuration on startup
- Routes AWS calls appropriately

## Overview
A batteries-included monorepo template with service-oriented architecture, featuring:
- **Dependency Injection** using `dependency-injector` library
- **Multiple Entry Points** per service (API, Celery, Lambda)
- **Service Discovery** for automatic route/task registration
- **Event Backbone** with Celery + Redis
- **Pants Build System** for dependency management and Lambda packaging
- **Infrastructure as Code** with Pulumi
- **Database** integration with Supabase
- **Security Groups** for API route authorization

## Core Architecture Principles
1. **Service-Oriented**: Each service is independently deployable
2. **Module-Based**: Services contain internal modules for business logic
3. **Dependency Injection**: IoC container pattern with `dependency-injector`
4. **Config Mixin**: Hierarchical configuration with type safety
5. **Event-Driven**: Loose coupling via event backbone
6. **Auto-Discovery**: Entry points discover and aggregate service components

## Project Structure

```
pantstack/
├── .localstack/               # LocalStack configuration
│   └── init/
│       └── ready.d/          # Initialization scripts
│           ├── 01-create-resources.sh
│           └── 02-seed-data.sh
│
├── config/                    # Configuration files
│   ├── defaults.yaml         # Base configuration
│   └── environments/         # Environment-specific
│       ├── development.yaml
│       ├── test.yaml
│       ├── staging.yaml
│       └── production.yaml
│
├── entry_points/              # Centralized entry points
│   ├── api/                   # Single API aggregator
│   │   ├── main.py           # FastAPI app creation
│   │   ├── registry.py       # Route discovery
│   │   └── run.py            # Uvicorn runner
│   │
│   ├── celery_worker/        # Single Celery worker
│   │   ├── app.py           # Celery app configuration
│   │   ├── registry.py      # Task discovery
│   │   └── run.py           # Worker runner
│   │
│   └── event_processor/      # Lambda handlers
│       ├── registry.py      # Handler discovery
│       └── lambda_handler.py
│
├── services/                 # Business services
│   ├── {service_name}/
│   │   ├── src/             # Entry point definitions
│   │   │   ├── api/         # API route definitions
│   │   │   │   ├── routes.py
│   │   │   │   └── manifest.py
│   │   │   ├── tasks/       # Celery task definitions
│   │   │   │   ├── tasks.py
│   │   │   │   └── manifest.py
│   │   │   └── lambdas/     # Lambda functions
│   │   │       ├── BUILD
│   │   │       └── {function}/
│   │   │           ├── handler.py
│   │   │           └── BUILD
│   │   │
│   │   ├── lib/            # Business logic
│   │   │   ├── core/       # Core infrastructure
│   │   │   │   ├── container.py
│   │   │   │   ├── config.py
│   │   │   │   └── events.py
│   │   │   └── modules/    # Business modules
│   │   │       └── {module}/
│   │   │           ├── services.py
│   │   │           ├── repositories.py
│   │   │           └── schemas.py
│   │   │
│   │   ├── config/         # Configuration
│   │   │   ├── settings.yaml
│   │   │   └── environments/
│   │   │
│   │   ├── infrastructure/ # Pulumi IaC
│   │   ├── tests/
│   │   └── BUILD
│   │
│   ├── auth/              # Example service
│   ├── orders/
│   └── notifications/
│
├── shared/                # Shared infrastructure
│   ├── core/
│   │   ├── registry.py   # Service registry base
│   │   ├── security.py   # Security groups
│   │   ├── discovery.py  # Auto-discovery
│   │   ├── config.py     # Config mixin base
│   │   ├── environment.py # Environment detection
│   │   ├── config_strategy.py # Config loading strategies
│   │   ├── aws_factory.py # AWS client factory
│   │   └── health.py     # Health checks & validation
│   │
│   └── utils/
│
├── lambda_layers/         # Shared Lambda layers
│   ├── core/
│   │   ├── BUILD
│   │   └── python/
│   └── monitoring/
│
└── platform/             # Platform infrastructure
    └── infra/
        └── foundation/
```

## Key Components

### 1. Dependency Injection Container

Each service has a DI container that manages dependencies:

```python
class ServiceContainer(containers.DeclarativeContainer):
    # Configuration
    config = providers.Singleton(ServiceConfig.from_environment)

    # Infrastructure
    database = providers.Singleton(SupabaseClient, config=config.provided.database)
    redis = providers.Singleton(RedisClient, config=config.provided.redis)
    event_backbone = providers.Singleton(EventBackbone, config=config.provided.events)

    # Business modules
    auth_service = providers.Factory(AuthService, ...)
    user_service = providers.Factory(UserService, ...)
```

### 2. Config Mixin Pattern

Type-safe hierarchical configuration with Pydantic:

```python
class ConfigMixin(Generic[T]):
    """Mixin to inject configuration into any class"""
    @property
    def config(self) -> T:
        return self._config_instance

class ServiceConfig(BaseConfig):
    """Service configuration with nested configs"""
    database: DatabaseConfig
    redis: RedisConfig
    celery: CeleryConfig
    aws: AWSConfig
```

### 3. Security Groups for Routes

API routes are organized by security level:
- **`public`** - No authentication required
- **`authenticated`** - Requires valid JWT/session
- **`admin`** - Requires admin role
- **`internal`** - Service-to-service only

### 4. Service Discovery

Entry points automatically discover and register components:

```python
class APIRegistry(ServiceRegistry):
    def discover_services(self):
        # Auto-discover all service API routes
        for service in services:
            manifest = load_manifest(service, "api")
            self.register_routes(manifest)

class CeleryRegistry(ServiceRegistry):
    def discover_services(self):
        # Auto-discover all Celery tasks
        for service in services:
            manifest = load_manifest(service, "tasks")
            self.register_tasks(manifest)
```

### 5. Event Backbone

Unified event publishing to multiple targets:

```python
class EventBackbone:
    async def publish(event_type: EventType, data: dict, target: str = "all"):
        # Publish to: Redis, Celery, SQS, EventBridge
```

### 6. Lambda with Pants

Each Lambda function is packaged independently:

```python
# BUILD file
python_awslambda(
    name="order_processor",
    handler="handler:lambda_handler",
    runtime="python3.12",
    dependencies=["//services/orders/lib:core"],
    layers=["//lambda_layers/core:layer"]
)
```

### 7. Environment Detection & Configuration Loading

Smart configuration based on runtime environment:

```python
# Automatic environment detection
from shared.core.environment import EnvironmentDetector
env = EnvironmentDetector.detect()  # Returns: LOCALSTACK, DEVELOPMENT, etc.

# Configuration with strategy pattern
from shared.core.config_strategy import ConfigLoader
config = ConfigLoader.load(AuthConfig, "auth")  # Auto-selects strategy

# AWS clients with auto-detection
from shared.core.aws_factory import get_aws_factory
aws = get_aws_factory()
dynamodb = aws.dynamodb  # Routes to LocalStack if detected
```

### 8. AWS Client Factory

Intelligent AWS service clients:

```python
class AWSClientFactory:
    def get_client(self, service: str):
        if self.config.localstack_enabled:
            # Auto-route to LocalStack
            return boto3.client(service, endpoint_url="http://localhost:4566")
        return boto3.client(service)
```

### 9. Health Checks & Validation

Service readiness and configuration validation:

```python
# Wait for dependencies
await ServiceHealth.wait_for_dependencies(["redis", "postgres", "localstack"])

# Validate configuration
ConfigValidator.assert_valid(config, environment)

# Startup validation
results = await StartupValidator.validate_startup(config)
```

## Service Template

Each service follows this structure:

### API Routes (`src/api/`)
- Define route handlers
- Create manifest for discovery
- Specify security groups

### Celery Tasks (`src/tasks/`)
- Define async tasks
- Create manifest for discovery
- Handle events from queue

### Lambda Functions (`src/lambdas/`)
- Isolated handlers
- Pants BUILD configuration
- Minimal dependencies

### Business Logic (`lib/`)
- Core container setup
- Business modules
- Repository pattern
- Service layer

## Implementation Phases

### Phase 1: Core Infrastructure
- Shared registry system
- Config mixin base
- Security middleware
- Discovery utilities

### Phase 2: Entry Points
- API with route aggregation
- Celery with task discovery
- Lambda handler pattern

### Phase 3: Reference Service
- Auth service implementation
- Complete CRUD example
- Event publishing
- Testing setup

### Phase 4: Build & Deploy
- Pants configuration
- GitHub Actions workflows
- Pulumi infrastructure
- Documentation

## Technology Stack

- **API Framework**: FastAPI
- **Task Queue**: Celery + Redis
- **Database**: Supabase (local and cloud - PostgreSQL + Auth + Storage + Realtime)
- **Event Bus**: Redis Pub/Sub + AWS EventBridge
- **Build System**: Pants 2.28.0
- **IaC**: Pulumi
- **Container**: Docker
- **CI/CD**: GitHub Actions
- **Cloud**: AWS (ECS, Lambda, S3, SQS, DynamoDB)
- **Local AWS**: LocalStack 3.7
- **Dependency Injection**: dependency-injector
- **Configuration**: Pydantic + Strategy Pattern
- **Testing**: pytest + LocalStack + Supabase

## Development Workflow

1. **Setup Tools**: `make setup` (first-time setup)
2. **Create Service**: `make new-service S=myservice`
3. **Add Module**: Define in `lib/modules/`
4. **Add Routes**: Create in `src/api/` with manifest
5. **Add Tasks**: Create in `src/tasks/` with manifest
6. **Add Lambda**: Create in `src/lambdas/` with BUILD
7. **Test**: `pants test ::` or `make test`
8. **Package**: `pants package ::`
9. **Deploy**: `pulumi up`

## Configuration Management

### Configuration Hierarchy
Configuration is loaded in priority order:
1. Command-line arguments
2. Environment variables
3. `.env` file
4. Environment-specific YAML (`config/environments/{env}.yaml`)
5. Default YAML (`config/defaults.yaml`)
6. Hardcoded defaults in code

### Environment Detection
The system automatically detects the runtime environment:
- **LocalStack**: When `LOCALSTACK=true` or LocalStack is running
- **Development**: Default for local development
- **Test**: When `CI=true` or during test runs
- **Staging/Production**: Based on `ENVIRONMENT` variable

### Configuration Loading Strategies
Different strategies for each environment:
- **LocalStackStrategy**: Auto-configures for LocalStack endpoints
- **DevelopmentStrategy**: Loads from YAML files with auto-detection
- **TestStrategy**: Optimized for testing with mocked services
- **ProductionStrategy**: Loads from SSM Parameter Store
- **StagingStrategy**: Similar to production with debug enabled

### LocalStack Integration
When LocalStack is detected:
- All AWS service calls automatically route to `http://localhost:4566`
- Dummy AWS credentials are used
- Resources are auto-created via init scripts
- Test data is seeded automatically

### Configuration Validation
On startup, the system:
- Validates required fields are present
- Checks environment-specific constraints
- Ensures secrets are not default values in production
- Verifies service dependencies are available

## Supabase Integration

### Local Development Setup
Supabase provides a complete backend platform locally:

```bash
# Initialize Supabase (one-time)
supabase init

# Start Supabase services
supabase start

# Stop Supabase services
supabase stop

# Check status
supabase status

# Reset database
supabase db reset
```

### Supabase Services & Ports
- **API**: http://localhost:54321 (REST API)
- **GraphQL**: http://localhost:54321/graphql/v1
- **Auth**: http://localhost:54321/auth/v1
- **Storage**: http://localhost:54321/storage/v1
- **Realtime**: ws://localhost:54321/realtime/v1
- **PostgreSQL**: postgresql://postgres:postgres@localhost:54322/postgres
- **Studio**: http://localhost:54323 (Database GUI)
- **Inbucket**: http://localhost:54324 (Email testing)

### Default Keys (Local Development Only)
```bash
# Anon Key (public)
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0

# Service Role Key (admin)
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU
```

### Database Migrations
```bash
# Create a new migration
supabase migration new <migration_name>

# Apply migrations
supabase db push

# Generate types from database
supabase gen types typescript --local > types/database.ts
```

### Docker Integration
Services in Docker containers access Supabase via `host.docker.internal`:
- API URL: `http://host.docker.internal:54321`
- Database: `postgresql://postgres:postgres@host.docker.internal:54322/postgres`

## LocalStack Development

### Automatic Resource Creation
LocalStack init scripts automatically create:
- DynamoDB tables with indexes
- S3 buckets with CORS policies
- SQS queues with DLQs
- EventBridge event buses and rules
- SSM parameters for secrets
- Lambda function placeholders
- CloudWatch log groups

**Important**: LocalStack init scripts must be executable:
```bash
chmod +x .localstack/init/ready.d/*.sh
```

### Development Commands
```bash
# Tool Management
make setup              # Interactive tool installation
make check-tools        # Check all tools are installed
make install-uv         # Install uv package manager
make install-pants      # Install Pants build system

# LocalStack management
make localstack-up       # Start LocalStack with init
make localstack-init     # Initialize resources
make localstack-reset    # Reset to clean state
make localstack-logs     # View LocalStack logs

# Configuration
make config-init        # Initialize config files
make config-validate    # Validate configuration
make config-show        # Display resolved config

# Development
make dev-api           # Run API with LocalStack
make dev-worker        # Run Celery worker
make dev-shell         # Interactive shell with AWS clients

# Testing
make test               # Run all tests with Pants
make test-unit          # Run unit tests only
make test-integration   # Run integration tests only
pants test services/auth/::  # Test specific service
pants test --tags='unit'     # Run tests by tag

# AWS/LocalStack inspection
make ls-tables         # List DynamoDB tables
make ls-queues         # List SQS queues
make ls-buckets        # List S3 buckets
make ls-params         # List SSM parameters
```

### State Persistence
LocalStack maintains state across restarts:
- `PERSISTENCE=1` enables state saving
- Snapshots saved on shutdown
- Automatically restored on startup
- Volume mount for data persistence

## Testing Infrastructure

### Test Organization
Tests are managed using Pants build system with a dedicated `test` resolve for dependencies:

```python
# BUILD file example
python_tests(
    name="test_services",
    sources=["test_services.py"],
    tags=["unit", "auth"],
    resolve="test",
    dependencies=[
        "//3rdparty/python:test_reqs#boto3",
        "//3rdparty/python:test_reqs#pytest",
    ],
)
```

### Test Categories
- **Unit Tests**: Per module with mocked dependencies (`tags=["unit"]`)
- **Integration Tests**: Service-level with test containers (`tags=["integration"]`)
- **E2E Tests**: Full stack with LocalStack (`tags=["e2e", "slow"]`)
- **Contract Tests**: API schema validation (`tags=["contract"]`)
- **Load Tests**: K6 for performance testing (`tags=["performance"]`)

### Test Resolves
The project uses a dedicated `test` resolve to isolate test dependencies:
- `3rdparty/python/requirements-test.txt`: Common test dependencies
- `3rdparty/python/requirements-{module}-test.txt`: Module-specific test deps
- `lockfiles/test.lock`: Locked test dependencies

### Running Tests
```bash
# Run all tests
pants test ::

# Run tests for specific service
pants test services/auth/::

# Run tests by tag
pants test --tags='unit'          # Unit tests only
pants test --tags='integration'    # Integration tests only
pants test --tags='-slow'          # Exclude slow tests

# Run with coverage
pants test --test-use-coverage ::

# Run specific test file
pants test services/auth/tests:test_services
```

### Test Structure
```
services/{service}/tests/
├── BUILD                 # Test configuration
├── conftest.py          # Pytest fixtures
├── unit/                # Unit tests
│   ├── test_services.py
│   └── test_repositories.py
├── integration/         # Integration tests
│   └── test_api.py
└── e2e/                # End-to-end tests
    └── test_workflows.py
```

## Deployment Strategy

- **Dev**: Auto-deploy from `dev` branch
- **Staging**: Deploy from `main` with approval
- **Production**: Tagged releases only
- **Rollback**: Blue-green deployments
- **Monitoring**: CloudWatch + OpenTelemetry

## Security Considerations

- **Authentication**: JWT with refresh tokens (Supabase Auth + custom)
- **Authorization**: Role-based (RBAC) with row-level security
- **Secrets**: Never in code, use AWS Secrets Manager or Supabase Vault
- **API Security**: Rate limiting, CORS, CSP
- **Data**: Encryption at rest and in transit

## Known Issues & Solutions

### LocalStack Script Permissions
**Issue**: LocalStack init scripts fail with permission denied.
**Solution**: Make scripts executable before starting LocalStack:
```bash
chmod +x .localstack/init/ready.d/*.sh
```

### Docker to Supabase Connectivity
**Issue**: Containers can't connect to Supabase on localhost.
**Solution**: Use `host.docker.internal` instead of localhost in Docker containers:
```yaml
environment:
  - DB_SUPABASE_URL=http://host.docker.internal:54321
```

### Environment Variable Precedence
**Issue**: Conflicting database configuration between .env files.
**Solution**: Priority order:
1. Docker environment variables
2. .env file
3. .env.local file
4. Default values in docker-compose.yml

### Supabase Docker Image
**Issue**: `supabase/postgres:15` image not found.
**Solution**: Use standard `postgres:15-alpine` or run Supabase via CLI instead of Docker.

---

## Setup and Installation Tools

### Tool Requirements
The project requires the following tools:
- **Python**: 3.12
- **uv**: Fast Python package installer (replaces pip)
- **Pants**: 2.28.0 build system
- **Docker**: Container runtime
- **Docker Compose**: Multi-container orchestration
- **AWS CLI**: AWS service interaction
- **Pulumi**: Infrastructure as Code
- **Supabase CLI**: Local backend platform
- **GitHub CLI**: Repository management
- **LocalStack**: Local AWS emulation

### Automated Setup
```bash
# Interactive setup (recommended)
make setup

# Quick setup (non-interactive)
make setup-quick

# Verify installation
make check-tools
```

### Setup Scripts
- `scripts/setup-tools.sh`: Interactive tool installer with OS detection
- `scripts/quick-setup.sh`: Non-interactive installer for CI/automation
- `scripts/setup/verify-tools.sh`: Tool verification and version checking

## Implementation Progress

### Core Infrastructure
- [x] Create `shared/core/` directory structure
- [x] Implement `registry.py` base classes
- [x] Implement `discovery.py` auto-discovery
- [x] Implement `security.py` middleware
- [x] Implement `config.py` mixin base
- [x] Add `dependency-injector` to requirements

### Entry Points
- [x] Create `entry_points/api/` structure
- [x] Implement API registry and discovery
- [x] Create main API application
- [x] Add run script for API server
- [x] Create `entry_points/celery_worker/` structure
- [x] Implement Celery registry and discovery
- [ ] Create `entry_points/event_processor/` structure (deferred)
- [ ] Implement Lambda handler pattern (deferred)

### CLI Management Tools
- [x] Create CLI structure (`cli/` directory)
- [x] Design service management commands
- [x] Design module management commands
- [x] Plan dependency management with uv
- [ ] Implement `pantstack` CLI commands (deferred - using Make for now)
- [ ] Add interactive service creation wizard (deferred)
- [ ] Create module scaffolding templates (deferred)

### Config System
- [x] Create config mixin implementation
- [x] Setup Pydantic schemas
- [x] Create environment-specific configs
- [x] Implement config validation
- [x] Add environment detection
- [x] Create config loading strategies
- [x] Implement LocalStack auto-configuration
- [x] Add health checks and validation

### Reference Service (Auth)
- [x] Create `services/auth/` structure
- [x] Implement DI container with smart config loading
- [x] Create auth module with service/repository
- [x] Create user module with service/repository
- [x] Add API routes with manifest
- [x] Implement event backbone integration
- [x] Add Celery tasks with manifest
- [x] Add Lambda handlers (verify_token, process_signup, token_refresh)
- [x] Setup testing infrastructure

### Build System
- [x] Configure Pants 2.28.0 for services
- [x] Setup `python_awslambda` targets
- [x] Create Lambda BUILD files
- [x] Add packaging commands to Makefile
- [x] Configure Lambda resolves
- [x] Create test resolve for isolated test dependencies
- [x] Setup BUILD files for all test directories
- [x] Configure test tags (unit, integration, e2e, slow)
- [x] Add Python source targets for test modules
- [x] Configure test timeouts for slow tests

### Infrastructure (Pulumi)
- [x] Update foundation infrastructure with Redis and EventBridge
- [x] Create service infrastructure template (auth)
- [x] Setup Lambda deployment configuration
- [x] Configure Celery workers on ECS
- [x] Setup Redis cluster
- [x] Add SSM Parameter Store integration

### CI/CD (GitHub Actions)
- [x] Update CI workflow for new structure
- [x] Create Lambda deployment workflow
- [x] Setup service deployment workflow
- [x] Add testing stages with Pants
- [x] Configure environment promotions
- [x] Add enhanced CI workflow (ci-enhanced.yml)
- [x] Create Lambda deployment workflow (deploy-lambda.yml)
- [x] Setup test result reporting
- [x] Add coverage reporting
- [x] Configure artifact management

### Documentation
- [x] Update README with new structure
- [x] Create service development guide
- [x] Document API patterns
- [x] Document deployment process
- [x] Add architecture diagrams
- [x] Create tools-requirements.md
- [x] Document setup process
- [x] Add testing documentation
- [x] Document Pants build system usage

### Testing
- [x] Setup test containers
- [x] Create test fixtures
- [x] Add integration tests
- [x] Setup LocalStack for AWS testing
- [x] Add pytest configuration
- [x] Create Pants BUILD files for all test directories
- [x] Implement test resolve for dependency isolation
- [x] Add test requirements management
- [x] Create shared test utilities
- [x] Setup CLI command tests
- [x] Add AWS factory tests with moto
- [x] Create container DI tests
- [x] Add environment detection tests
- [x] Setup logging infrastructure tests
- [x] Create integration test suite
- [x] Add E2E test structure

### LocalStack & Development
- [x] Create LocalStack initialization scripts
- [x] Add resource auto-creation
- [x] Implement seed data management
- [x] Configure state persistence
- [x] Add development helper commands
- [x] Create AWS client factory with auto-detection
- [x] Implement environment parity mechanisms
- [x] Fix script permission issues

### Configuration Management
- [x] Implement environment detection
- [x] Create configuration strategies
- [x] Add configuration validation
- [x] Setup configuration hierarchy
- [x] Create environment config files
- [x] Add .env templates

### Supabase Integration
- [x] Replace PostgreSQL container with Supabase CLI
- [x] Update docker-compose.yml for Supabase connectivity
- [x] Configure host.docker.internal for container access
- [x] Document local development keys and endpoints
- [x] Add Supabase commands to development workflow

### Docker Compose Updates
- [x] Remove PostgreSQL container
- [x] Add host.docker.internal configuration
- [x] Update environment variables for Supabase
- [x] Fix service dependencies

---

**Last Updated**: 2025-09-20
**Status**: Production-Ready with LocalStack & Supabase Integration (CLI enhancements deferred)
**Summary**:
- ✅ Service-oriented architecture with DI containers
- ✅ Auto-discovery for routes and tasks
- ✅ Security group-based routing
- ✅ Lambda functions with Pants packaging
- ✅ Celery workers with Redis broker
- ✅ Comprehensive Pulumi infrastructure
- ✅ GitHub Actions CI/CD pipelines
- ✅ Testing infrastructure with Pants build system
- ✅ Docker containerization for all services
- ✅ LocalStack integration for local AWS services
- ✅ Supabase for complete backend platform (DB, Auth, Storage, Realtime)
- ✅ Environment-aware configuration management
- ✅ Smart AWS client factory with auto-detection
- ✅ Health checks and startup validation
- ✅ Complete development helper commands
- ✅ Full local-to-cloud deployment parity
- ✅ Automated tool installation and setup
- ✅ Comprehensive test suite with BUILD files
- ✅ Test resolve for dependency isolation
- ✅ CLI management tool structure
- ✅ uv package manager integration
