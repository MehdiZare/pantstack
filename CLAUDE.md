# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is Pantstack, a batteries-included monorepo template using:
- **Pants** build system for service management and dependency resolution
- **Cookiecutter/Cruft** for template instantiation
- **FastAPI** for service APIs
- **Pulumi** for Infrastructure as Code on AWS
- **GitHub Actions** for CI/CD

The template provides true service independence with per-service infrastructure, packaging, tests, and dedicated Pants resolvers, while allowing safe cross-service reuse via public facades.

## Template Usage

This repository serves as a Cookiecutter template for creating new monorepo projects.

### Publishing as a Template (Template Authors)

Prerequisites:
- GitHub CLI installed: `gh auth login`
- Add workflow scope: `gh auth refresh -s workflow` (required for pushing GitHub Actions workflows)

Steps:
1. Copy `.env.example` to `.env` and replace `{{ cookiecutter.* }}` placeholders with actual values
2. Run `make init-template` to publish to GitHub as a template

### Creating Projects from Template (Template Users)

```bash
# Interactive wizard (recommended)
make quickstart

# Or directly create from this template
make new-project

# Or use from GitHub (after publishing)
cruft create gh:MehdiZare/pantstack
```

### Template Management Commands
```bash
# First-time setup as a template
make init-template      # Publish this repo as a template

# Show template usage guide
make template-help

# Create new project from template
make new-project        # Local template
make create-project     # Remote template (requires env vars)
```

## Essential Commands

### Development Workflow
```bash
# Install Pants build system
make boot
# Add to PATH: export PATH="$HOME/.local/bin:$PATH"

# Format, lint, and typecheck all code
make fmt
make lint

# Run all tests
make test

# Test and package a specific service
make mod S=api

# Generate/update Pants lockfiles
make locks
```

### Service Management
```bash
# Create a new service (scaffolds structure + BUILD files)
make new-service S=orders

# Create service in feature branch with PR
make gh-new-service-pr S=orders
```

### Local Development
```bash
# Start local services with docker-compose
make up

# Tear down local services
make down
```

### Infrastructure & Deployment
```bash
# Bootstrap foundation infrastructure (first-time setup)
# Requires filled .env file
make bootstrap

# Initialize Pulumi stacks for all services
make seed-stacks

# Deploy a service stack locally
make stack-up S=api ENV=test

# Preview changes before deployment
make stack-preview S=api ENV=prod

# Verify deployed stack
make stack-verify S=api ENV=test

# Trigger GitHub Actions deployment
make gha-deploy S=api ENV=prod
```

## Architecture

### Repository Structure

```
pantstack/
├── services/              # Independent microservices
│   ├── agent/            # Agent service with worker capabilities
│   ├── auth/             # Authentication service
│   ├── event_backbone/   # Event processing infrastructure
│   ├── web/              # Web application service
│   └── api/              # API gateway service
├── entry_points/         # Docker entry points & service aggregation
│   ├── api/              # Main API that aggregates all services
│   ├── celery_worker/    # Celery worker entry point
│   └── event_processor/  # Event processing entry point
├── shared/               # Cross-service shared libraries
│   ├── core/             # Core utilities and abstractions
│   ├── utils/            # Common utility functions
│   └── tests/            # Shared test utilities
├── stack/                # Platform-level infrastructure & libraries
│   ├── infra/            # Infrastructure as Code
│   │   ├── foundation/   # AWS foundation (ECR, OIDC, IAM roles)
│   │   └── components/   # Reusable infrastructure components
│   ├── libs/shared/      # Stack-specific shared libraries
│   ├── agents/           # Agent configurations
│   └── events/           # Event infrastructure libraries
├── 3rdparty/python/      # Python dependencies management
├── tests/                # Repository-wide tests
│   ├── integration/      # Cross-service integration tests
│   └── template/         # Template validation tests
├── cli/                  # CLI tools for repo management
└── scripts/              # Build and deployment scripts
```

### Service Structure
Each service under `services/` follows Domain-Driven Design and contains:
```
services/<service_name>/
├── app/                  # Application layer
│   ├── api/              # FastAPI endpoints and routers
│   │   └── main.py       # Service entry point
│   └── worker/           # Background workers (Celery, etc.)
│       └── run.py        # Worker entry point
├── domain/               # Core business logic (DDD)
│   ├── models/           # Domain models and entities
│   ├── services/         # Domain services
│   └── ports/            # Interface definitions (hexagonal architecture)
├── adapters/             # External integrations
│   └── repositories/     # Data persistence adapters
├── public/               # Public API exposed to other services
│   └── __init__.py       # Service facade
├── infrastructure/       # Service-specific IaC (Pulumi)
│   ├── Pulumi.yaml       # Pulumi project config
│   └── __main__.py       # Infrastructure definitions
├── lib/                  # Service-specific libraries
├── tests/                # Service tests
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
├── BUILD                 # Pants build configuration
├── Dockerfile.api        # API container definition
└── Dockerfile.worker     # Worker container definition
```

### Dependency Resolution
The monorepo uses Pants resolves for complete service isolation:
- Each service has separate `{service}_core` and `{service}_api` resolves
- Dependencies defined in `3rdparty/python/requirements-{service}-{layer}.txt`
- Lockfiles generated to `lockfiles/` directory
- Cross-service dependencies allowed only through public facades
- Services are truly independent with their own Python environments

### Image Tagging Strategy
- Single ECR repository per project
- Images tagged: `{service}-{branch}-{sha}` and `{service}-v{version}`
- Worker images: `{service}-worker-{branch}-{sha}`

## CI/CD Pipeline

### Branch Strategy
- `dev` branch: Prereleases (1.2.0-dev.3), deploys to test environment
- `main` branch: Stable releases (1.2.0), deploys to production
- Feature branches: Create PR preview stacks

### Workflow Files
- `.github/workflows/ci.yml` - Main CI pipeline (lint, test, package)
- `.github/workflows/auto-deploy-dev.yml` - Auto-deploy dev to test
- `.github/workflows/auto-deploy-main.yml` - Auto-deploy main to prod
- `.github/workflows/pr-preview.yml` - Deploy PR preview stacks
- `.github/workflows/semantic-pr.yml` - Enforce conventional commits

### Versioning
Uses semantic-release with conventional commits:
- `feat(service):` → minor bump
- `fix(service):` → patch bump
- `feat!:` → major bump (breaking change)
- Override with labels: `release:major`, `release:minor`, `release:patch`, `release:skip`

## Key Configuration Files

- `pants.toml` - Pants configuration and Python resolves
- `cookiecutter.json` - Template variables for project instantiation
- `.env` - Environment variables (copy from `.env.example`)
- `docker-compose.yml` - Local development stack
- `.releaserc.json` - Semantic release configuration
- `Pulumi.yaml` files in each service's infrastructure directory

## Testing Approach

Tests are run via Pants with service-specific test resolves:
```bash
# Run all tests
pants test ::

# Run specific service tests
pants test services/auth::

# Run with coverage
pants test --test-use-coverage services/web::

# Run integration tests
pants test tests/integration::
```

## Service Public Facades

Services expose public APIs through `public/` directories. Other services can depend on these facades but not on internal implementations. This ensures:
- Clear service boundaries
- Stable inter-service contracts
- Independent service evolution
- True microservice isolation

## Infrastructure Patterns

Each service's infrastructure (`services/{service}/infrastructure/__main__.py`) typically includes:
- ECS Fargate services with ALB
- SQS queues for async processing
- S3 buckets for storage
- Service-specific VPC and networking
- IAM roles with least privilege

Foundation infrastructure (`stack/infra/foundation/`) provides:
- ECR repository
- GitHub OIDC provider
- CI/CD IAM roles
- Shared networking components (if needed)

## Service Creation

To create a new service:
```bash
# Scaffold a new service with all necessary structure
make new-service S=orders

# This creates:
# - services/orders/ with complete DDD structure
# - BUILD file with proper Pants configuration
# - Infrastructure templates
# - Test scaffolding
```

## Key Principles

1. **Service Independence**: Each service is a bounded context with its own Pants resolver
2. **Public Facades**: Inter-service communication only through `public/` directories
3. **Shared Libraries**: Common code lives in `shared/` and `stack/libs/`
4. **Entry Point Aggregation**: `entry_points/api/` discovers and aggregates all service APIs
5. **Infrastructure Isolation**: Each service manages its own cloud resources
