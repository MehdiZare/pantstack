# Pantstack (services-first)

Pantstack is a batteries-included monorepo template for building modular microservices with Pants, FastAPI, Pulumi on AWS, and GitHub Actions.

## Key Features
- **Multi-module services** with internal modularity and external cohesion
- **Service independence** via per-service resolves, infrastructure, and tests
- **Selective module loading** for optimized entry points (API, Lambda, Worker)
- **Safe cross-service communication** via `public/` facades
- **Single ECR repository** with structured tagging
- **Comprehensive CI/CD** with PR preview stacks and semantic versioning
- **Infrastructure as Code** with Pulumi Cloud (Free tier)

## Architecture Overview

### Core Concepts

**Services** are bounded contexts that encapsulate related business capabilities:
- Each service owns its data, infrastructure, and deployment lifecycle
- Services communicate only through well-defined public interfaces
- Examples: `auth` (authentication), `web` (frontend), `api` (gateway), `agent` (workers)

**Modules** are internal components within a service:
- Modules group related functionality within a service boundary
- Modules can directly interact with other modules in the same service
- Modules enable gradual service decomposition
- Examples: `auth/lib/modules/users`, `auth/lib/modules/sessions`, `auth/lib/modules/tokens`

**Entry Points** are deployment targets with selective module loading:
- **API**: Full service with all modules for HTTP endpoints
- **Lambda**: Lightweight functions with only required modules
- **Worker**: Background processors with task-specific modules
- **CLI**: Administrative tools with management modules

**Public Facades** define service contracts:
- Located in `services/{service}/public/`
- Expose stable APIs for cross-service communication
- Hide internal implementation details
- Enable service evolution without breaking contracts

### Architecture Principles

1. **Service Autonomy**: Services are independently deployable with isolated dependencies
2. **Module Cohesion**: Related functionality stays together within service boundaries
3. **Selective Loading**: Entry points load only the modules they need
4. **Contract-First**: Services interact through explicit, versioned contracts
5. **Progressive Complexity**: Start simple, add modules as services grow

## Testing

### Running Tests with Pants

All tests in this project are managed through the Pants build system.

```bash
# Bootstrap Pants (first time only)
make boot

# Run all tests
make test

# Run specific test targets
pants test services/auth::           # All auth service tests
pants test tests/integration::       # All integration tests
pants test tests/template::          # Template validation tests

# Run tests with coverage
pants test --test-use-coverage services/auth::

# Run tests by tag
pants test --tag=unit ::             # Only unit tests
pants test --tag=integration ::      # Only integration tests
```

### Test Organization

- **Unit Tests**: Located in `services/*/tests/unit/` - Fast, isolated tests
- **Integration Tests**: Located in `tests/integration/` - Tests with external dependencies
- **Template Tests**: Located in `tests/template/` - Validate template structure

### Common Test Issues

1. **Import Errors**: Pants manages dependencies automatically. If you see import errors:
   - Check that the dependency is listed in the appropriate requirements file
   - Ensure the BUILD file includes the correct dependencies
   - Run `make locks` to regenerate lockfiles after adding dependencies

2. **Sandbox Issues**: Some tests require filesystem access. These tests have `run_goal_use_sandbox=False` in their BUILD configuration.

3. **Dependency Ambiguity**: If Pants reports ambiguous dependencies:
   - Add explicit dependencies to the test's BUILD configuration
   - Example: `"//3rdparty/python:test_reqs#requests"`

## Prerequisites

### Automated Setup (Recommended)
Run the setup script to install all required tools:
```bash
make setup        # Interactive setup with prompts
make setup-quick  # Quick setup without prompts
make check-tools  # Verify all tools are installed
```

### Required Tools
- **Python 3.11+** (3.11, 3.12, or newer)
- **uv** - Fast Python package installer
- **Docker & Docker Compose** - Container runtime
- **AWS CLI** - AWS service management
- **Pulumi** - Infrastructure as Code
- **Pants 2.28+** - Build system
- **Supabase CLI** - Database and auth management
- **GitHub CLI** - Repository management
- **jq** - JSON processing
- **cruft** - Template management

See [docs/tools-requirements.md](docs/tools-requirements.md) for detailed installation instructions.

## Quick Start (Template Author)

Prerequisites:
- GitHub CLI (`gh`) installed and authenticated: `gh auth login`
- Add workflow scope to GitHub CLI: `gh auth refresh -s workflow`

Steps to publish this as a template:

1) Create `.env` file with your configuration:
   ```bash
   cp .env.example .env
   # Edit .env and replace the cookiecutter placeholders with actual values:
   # GITHUB_OWNER=YourGitHubUsername
   # GITHUB_REPO=your-template-name
   # Leave GITHUB_TOKEN empty to use gh CLI authentication
   ```

2) Publish the template:
   ```bash
   make init-template
   ```
   This will:
   - Create/update the GitHub repository
   - Push code to `dev` (default) and `main` branches
   - Mark repository as a GitHub template
   - Configure repository metadata and topics

3) Your template is now ready at: `https://github.com/YourUsername/your-template-name`

**Note**: The template repository has workflows that are configured to skip execution to avoid failures. These workflows will automatically activate when users create their own projects from the template.

## Template Versioning

This template follows [Semantic Versioning](https://semver.org/). All changes from `dev` to `main` require a version label:

- **release:major** - Breaking changes (e.g., 1.0.0 → 2.0.0)
- **release:minor** - New features (e.g., 1.0.0 → 1.1.0)
- **release:patch** - Bug fixes (e.g., 1.0.0 → 1.0.1)
- **release:skip** - No version bump (docs, CI tweaks)

### For Template Maintainers
1. Make changes in feature branches, PR to `dev`
2. When ready to release, PR from `dev` to `main` with a version label
3. On merge, automatic GitHub release with changelog

### For Template Users
- Check releases: https://github.com/MehdiZare/pantstack/releases
- Use specific version: `cruft create gh:MehdiZare/pantstack --checkout v1.2.3`
- Update existing project: `cruft update` (if using cruft)

## Create a New Project from the Template

### Option A: Cookiecutter with Variable Substitution (Recommended)

This method prompts you for project-specific values and automatically replaces template variables.

1) Install Cruft (enhanced Cookiecutter):
   ```bash
   pipx install cruft  # or: pip install --user cruft
   ```

2) Create project from template:
   ```bash
   cruft create gh:MehdiZare/pantstack
   # You'll be prompted for:
   # - project_slug (your project name)
   # - github_owner (your GitHub username)
   # - aws_account_id, aws_region, pulumi_org, etc.
   ```

3) Set up the new project:
   ```bash
   cd your-project-name
   cp .env.example .env  # Edit with your actual credentials
   make bootstrap        # Creates GitHub repo, ECR, CI/CD setup
   make seed-stacks      # Initialize Pulumi stacks
   git push -u origin dev
   ```

### Option B: GitHub Template UI (Simple Copy)

This method creates a simple copy without variable substitution.

1) Go to https://github.com/MehdiZare/pantstack
2) Click "Use this template" → "Create a new repository"
3) Clone your new repository
4) Update `.env` file with your values (replace any remaining `cookiecutter placeholders` placeholders)
5) Run setup commands:
   ```bash
   make bootstrap
   make seed-stacks
   git push -u origin dev
   ```

### Option C: Local Template

If you have the template locally:
```bash
make new-project  # Interactive prompts for all values
```

## Commands You'll Use Often

### Service & Module Management
- `make new-service S=<name>` — Create a new service with standard structure
- `make new-module S=<service> M=<module>` — Add a module to an existing service (coming soon)
- `make mod S=web` — Test and package a service with all its modules

### Infrastructure & Deployment
- `make stack-up S=web ENV=test` — Deploy a service stack to an environment
- `make stack-outputs S=web ENV=test` — Show deployed stack outputs
- `make gha-deploy S=web ENV=prod` — Trigger GitHub Actions deployment

### Development Workflow
- `make fmt` — Format all code with Black and isort
- `make lint` — Run linting checks
- `make test` — Run all tests
- `make locks` — Regenerate dependency lockfiles

Note: Pants is installed via the official bootstrap script. Local targets use `./pants`.

## Versioning & Promotion

- Dev merges → prereleases (`1.2.0-dev.3`) + deploy to test
- Dev→main PR → Pulumi preview only (dry run)
- Main merges → stable releases (`1.2.0`) + deploy to prod
- See `VERSIONING.md` for PR title format and label overrides

## Project Structure

```
pantstack/
├── services/                    # Bounded context services
│   └── {service}/               # e.g., auth, web, api, agent
│       ├── app/                 # Application layer
│       │   ├── api/             # FastAPI HTTP endpoints
│       │   └── worker/          # Background workers (Celery)
│       ├── domain/              # Business logic (DDD)
│       │   ├── models/          # Domain entities
│       │   ├── services/        # Domain services
│       │   └── ports/           # Interface definitions
│       ├── adapters/            # External integrations
│       │   ├── repositories/    # Data persistence
│       │   └── clients/         # External service clients
│       ├── lib/                 # Service-specific libraries
│       │   └── modules/         # Internal service modules
│       │       └── {module}/    # Module implementation
│       │           ├── module.py     # Module interface
│       │           ├── routes.py     # Module API routes
│       │           ├── tasks.py      # Module async tasks
│       │           ├── handlers.py   # Module event handlers
│       │           └── schemas.py    # Module data models
│       ├── public/              # Service public API
│       │   └── __init__.py      # Service manifest & contracts
│       ├── infrastructure/      # Pulumi IaC for service
│       │   ├── __main__.py      # Infrastructure definition
│       │   └── Pulumi.yaml      # Stack configuration
│       └── tests/               # Service tests
│           ├── unit/            # Fast, isolated tests
│           └── integration/     # Service integration tests
├── entry_points/                # Aggregation & deployment targets
│   ├── api/                     # Main API gateway
│   ├── celery_worker/           # Task worker entry point
│   └── event_processor/         # Event handler entry point
├── stack/                       # Platform-level code
│   ├── libs/shared/             # Shared utilities
│   ├── events/                  # Event definitions
│   ├── agents/                  # Agent framework
│   └── infra/                   # Infrastructure components
│       ├── foundation/          # AWS foundation (VPC, ECR, IAM)
│       └── components/          # Reusable Pulumi components
├── shared/                      # Cross-service shared code
│   ├── core/                    # Core abstractions
│   └── utils/                   # Common utilities
├── 3rdparty/python/             # External dependencies
│   └── requirements-*.txt       # Per-service/resolver deps
├── tests/                       # Repository-level tests
│   ├── integration/             # Cross-service tests
│   └── template/                # Template validation
└── scripts/                     # Automation scripts
```

## Local Development (LocalStack & Supabase)

Spin up AWS mocks and run services locally:

1. **Start Supabase** (provides PostgreSQL, Auth, Storage):
   ```bash
   supabase start  # First time: pulls Docker images
   ```

2. **Start LocalStack & Redis**:
   ```bash
   make dev-up  # Starts LocalStack (S3, SQS, DynamoDB) and Redis
   ```

3. **Run services**:
   - `make dev-api-s S=web` — run the web API locally
   - `make dev-worker-s S=agent` — run the agent worker locally

4. **Stop services**:
   ```bash
   make dev-down    # Stops LocalStack and Redis
   supabase stop    # Stops Supabase services
   ```

Notes:
- LocalStack runs on `http://localhost:4566`
- Supabase Studio available at `http://localhost:54323`
- When `LOCALSTACK=true`, adapters auto‑configure to LocalStack and create queues/buckets/tables if missing.

## Template vs. Generated Projects

- This repository is a template. CI jobs that deploy are disabled here by default via guards.
- In generated projects, leave `TEMPLATE_REPO_SLUG` unset so deploy/preview workflows run normally.

## First-time Checklist

- Read and follow `SETUP_CHECKLIST.md`
- For Pulumi Cloud Free, set `PULUMI_ORG` to your username.
- Run `make bootstrap` and then `make seed-stacks`.

See `AGENTS.md` for an agents playbook covering structure, commands, and reusable components.
