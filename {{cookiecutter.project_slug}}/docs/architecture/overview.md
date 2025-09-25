# Architecture Overview

Pantstack is a batteries-included monorepo template designed for building layered services with modern DevOps practices.

## Core Principles

- **Service Independence**: Each service has its own resolves, infrastructure, packaging, and tests
- **Safe Cross-Service Reuse**: Services communicate via public facades and shared stack libraries
- **Infrastructure as Code**: Pulumi manages all cloud resources on AWS
- **Build System**: Pants provides efficient dependency management and module isolation
- **CI/CD First**: GitHub Actions automates testing, packaging, and deployment

## Technology Stack

### Build & Development
- **Pants 2.28.0**: Modern build system for Python monorepos
- **Python 3.12**: Primary development language
- **FastAPI**: High-performance web framework for APIs
- **Cookiecutter/Cruft**: Template instantiation and management

### Infrastructure
- **Pulumi**: Infrastructure as Code on AWS
- **AWS Services**: ECS Fargate, ALB, SQS, S3, ECR
- **Docker**: Container packaging and deployment
- **Pulumi Cloud**: State management (free tier)

### CI/CD
- **GitHub Actions**: Automated workflows
- **Semantic Release**: Automated versioning and changelog
- **GitHub OIDC**: Secure AWS authentication without long-lived credentials

## Repository Structure

```
pantstack/
├── modules/           # Service modules (api, admin, etc.)
│   └── {service}/
│       ├── backend/   # Service implementation
│       │   ├── api/   # FastAPI application
│       │   ├── service/  # Business logic
│       │   ├── worker/   # Async workers
│       │   ├── schemas/  # Data models
│       │   ├── public/   # Public facade
│       │   └── tests/    # Unit tests
│       └── infrastructure/  # Pulumi IaC
├── stack/             # Shared libraries
│   ├── libs/         # Common utilities
│   └── infra/        # Foundation infrastructure
├── 3rdparty/         # External dependencies
├── lockfiles/        # Dependency locks
└── docs/            # Documentation
```

## Key Design Decisions

### Module Isolation
Each service module is isolated with its own Python resolve, preventing accidental dependencies and ensuring true independence.

### Public Facades
Services expose stable APIs through `backend/public/` directories, ensuring clear boundaries and contracts between services.

### Single ECR Repository
All service images are stored in a single ECR repository with structured tagging: `{service}-{branch}-{sha}`.

### Environment Strategy
- `dev` branch → test environment (prereleases)
- `main` branch → production environment (stable releases)
- Feature branches → PR preview stacks

### Dependency Management
Pants resolves ensure each service has isolated dependencies while allowing controlled sharing through public facades and stack libraries.
