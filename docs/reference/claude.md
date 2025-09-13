# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is Pantstack, a batteries-included monorepo template using:
- **Pants** build system for module management and dependency resolution
- **Cookiecutter/Cruft** for template instantiation
- **FastAPI** for service APIs
- **Pulumi** for Infrastructure as Code on AWS
- **GitHub Actions** for CI/CD

The template provides true module independence with per-module infrastructure, packaging, and tests, while allowing safe cross-module reuse via public facades.

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
# Install Pants build system (version 2.28.0)
make boot
# Add to PATH: export PATH="$HOME/.local/bin:$PATH"

# Format, lint, and typecheck all code
make fmt
make lint

# Run all tests
make test

# Test and package a specific module
make mod M=api

# Generate/update Pants lockfiles
make locks
```

### Module Management
```bash
# Create a new module (scaffolds structure + BUILD files)
make new-module M=orders

# Create module in feature branch with PR
make gh-new-module-pr M=orders
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

# Initialize Pulumi stacks for all modules
make seed-stacks

# Deploy a module stack locally
make stack-up M=api ENV=test

# Preview changes before deployment
make stack-preview M=api ENV=prod

# Verify deployed stack
make stack-verify M=api ENV=test

# Trigger GitHub Actions deployment
make gha-deploy M=api ENV=prod
```

## Architecture

### Module Structure
Each module under `modules/` contains:
- `BUILD` - Pants build configuration defining resolves and dependencies
- `backend/` - Service implementation
  - `api/` - FastAPI application entry point
  - `service/` - Business logic
  - `worker/` - Async worker if needed
  - `schemas/` - Data models
  - `public/` - Public facade for cross-module use
  - `tests/` - Unit and integration tests
- `infrastructure/` - Pulumi IaC code (`__main__.py`)

### Dependency Resolution
The monorepo uses Pants resolves for isolation:
- Each module has separate `{module}_core` and `{module}_api` resolves
- Dependencies defined in `3rdparty/python/requirements-{module}-{layer}.txt`
- Lockfiles generated to `lockfiles/` directory
- Cross-module dependencies allowed only through public facades

### Image Tagging Strategy
- Single ECR repository per project
- Images tagged: `{module}-{branch}-{sha}` and `{module}-v{version}`
- Worker images: `{module}-worker-{branch}-{sha}`

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
- `feat(module):` → minor bump
- `fix(module):` → patch bump
- `feat!:` → major bump (breaking change)
- Override with labels: `release:major`, `release:minor`, `release:patch`, `release:skip`

## Key Configuration Files

- `pants.toml` - Pants configuration and Python resolves
- `cookiecutter.json` - Template variables for project instantiation
- `.env` - Environment variables (copy from `.env.example`)
- `docker-compose.yml` - Local development stack
- `.releaserc.json` - Semantic release configuration
- `Pulumi.yaml` files in each module's infrastructure directory

## Testing Approach

Tests are run via Pants with module-specific test resolves:
```bash
# Run all tests
pants test ::

# Run specific module tests
pants test modules/api/::

# Run with coverage
pants test --test-use-coverage modules/api/::
```

## Module Public Facades

Modules expose public APIs through `backend/public/` directories. Other modules can depend on these facades but not on internal implementations. This ensures:
- Clear module boundaries
- Stable inter-module contracts
- Independent module evolution

## Infrastructure Patterns

Each module's infrastructure (`modules/{module}/infrastructure/__main__.py`) typically includes:
- ECS Fargate services with ALB
- SQS queues for async processing
- S3 buckets for storage
- Module-specific VPC and networking
- IAM roles with least privilege

Foundation infrastructure (`platform/infra/foundation/`) provides:
- ECR repository
- GitHub OIDC provider
- CI/CD IAM roles
- Shared networking components (if needed)