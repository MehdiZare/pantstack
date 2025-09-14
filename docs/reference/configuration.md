# Configuration Reference

Complete reference for all Pantstack configuration files and environment variables.

## Environment Variables

### Core Configuration (.env)

```bash
# Project Configuration
PROJECT_NAME=pantstack
PROJECT_SLUG=pantstack
PROJECT_DESCRIPTION="Batteries-included monorepo"

# GitHub Configuration
GITHUB_OWNER=MehdiZare
GITHUB_REPO=pantstack
GITHUB_TOKEN=  # Optional, uses gh CLI if empty

# AWS Configuration
AWS_ACCOUNT_ID=123456789012
AWS_REGION=us-east-1
AWS_PROFILE=default  # Optional

# Pulumi Configuration
PULUMI_ORG=your-org
PULUMI_ACCESS_TOKEN=pul-xxxxx
PULUMI_BACKEND_URL=  # Optional, uses Pulumi Cloud if empty

# Container Registry
ECR_REGISTRY=123456789012.dkr.ecr.us-east-1.amazonaws.com
ECR_REPOSITORY=pantstack

# Python Configuration
PYTHON_VERSION=3.12

# Environment Settings
ENVIRONMENT=development  # development, staging, production
LOG_LEVEL=INFO
DEBUG=false
```

### Service-Specific Variables

```bash
# API Service
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
API_RELOAD=false
API_CORS_ORIGINS=["http://localhost:3000"]

# Database
DATABASE_URL=postgresql://user:pass@localhost/dbname
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
DATABASE_ECHO=false

# Redis Cache
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=
REDIS_MAX_CONNECTIONS=50

# AWS Services
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789012/queue
S3_BUCKET_NAME=pantstack-storage
DYNAMODB_TABLE_NAME=pantstack-data

# Authentication
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# External APIs
OPENAI_API_KEY=sk-xxxxx
STRIPE_API_KEY=sk_test_xxxxx
SENDGRID_API_KEY=SG.xxxxx
```

## Pants Configuration

### pants.toml

```toml
[GLOBAL]
pants_version = "2.28.0"
backend_packages = [
    "pants.backend.python",
    "pants.backend.python.lint.black",
    "pants.backend.python.lint.flake8",
    "pants.backend.python.lint.isort",
    "pants.backend.python.typecheck.mypy",
    "pants.backend.docker",
    "pants.backend.shell",
    "pants.backend.shell.lint.shellcheck",
    "pants.backend.shell.lint.shfmt",
]

[source]
root_patterns = [
    "/",
    "/modules/*",
    "/stack/*",
]

[python]
interpreter_constraints = ["CPython==3.12.*"]
enable_resolves = true

[python.resolves]
# Core resolves for services
api_core = "3rdparty/python/requirements-api-core.txt"
api_api = "3rdparty/python/requirements-api-api.txt"
api_test = "3rdparty/python/requirements-api-test.txt"

admin_core = "3rdparty/python/requirements-admin-core.txt"
admin_api = "3rdparty/python/requirements-admin-api.txt"
admin_test = "3rdparty/python/requirements-admin-test.txt"

# Shared libraries
common = "3rdparty/python/requirements-common.txt"
infrastructure = "3rdparty/python/requirements-infrastructure.txt"

[python.resolves_to_interpreter_constraints]
api_core = ["CPython==3.12.*"]
api_api = ["CPython==3.12.*"]
admin_core = ["CPython==3.12.*"]
admin_api = ["CPython==3.12.*"]

[python-infer]
use_rust_parser = true
imports = true
string_imports = true
string_imports_min_dots = 2

[test]
use_coverage = false
timeout_default = 60

[coverage-py]
report = ["console", "html", "xml"]
global_report = true

[black]
config = "pyproject.toml"

[flake8]
config = ".flake8"

[isort]
config = ".isort.cfg"

[mypy]
config = "mypy.ini"

[docker]
build_args = ["PYTHON_VERSION"]
default_repository = "{ecr_registry}/{ecr_repository}"
registries = {
    "ecr_registry" = {
        "address" = "${ECR_REGISTRY}",
        "default" = true,
    }
}

[shellcheck]
args = ["-x"]

[shfmt]
args = ["-i", "2", "-ci"]
```

### BUILD Files

#### Module BUILD
```python
# modules/api/BUILD
python_sources(
    name="lib",
    sources=["backend/**/*.py"],
    resolve="api_core",
    dependencies=[
        "stack/libs/common",
        "modules/auth/backend/public",
    ],
)

pex_binary(
    name="api",
    entry_point="backend/api/main.py",
    resolve="api_api",
    dependencies=[":lib"],
)

docker_image(
    name="docker",
    dependencies=[":api"],
    repository="pantstack",
    image_tags=["api-{version}", "api-latest"],
    instructions=[
        "FROM python:3.12-slim",
        "WORKDIR /app",
        "COPY api.pex /app/",
        'ENTRYPOINT ["/app/api.pex"]',
    ],
)

python_tests(
    name="tests",
    sources=["backend/tests/**/*.py"],
    resolve="api_test",
    dependencies=[":lib"],
)
```

## Pulumi Configuration

### Pulumi.yaml

```yaml
name: pantstack-api
runtime: python
description: API service infrastructure
config:
  pulumi:template: aws-python
```

### Pulumi.{env}.yaml

```yaml
# Pulumi.test.yaml
config:
  aws:region: us-east-1
  pantstack:environment: test
  pantstack:minCapacity: 1
  pantstack:maxCapacity: 3
  pantstack:cpu: 256
  pantstack:memory: 512
  pantstack:desiredCount: 2
  pantstack:healthCheckPath: /health
  pantstack:healthCheckInterval: 30
  pantstack:domain: test.pantstack.example.com
```

### Stack Configuration (Python)

```python
# modules/api/infrastructure/__main__.py
import pulumi
from pulumi import Config

config = Config()

# Get configuration values
environment = config.require("environment")
min_capacity = config.get_int("minCapacity") or 1
max_capacity = config.get_int("maxCapacity") or 10
cpu = config.get_int("cpu") or 256
memory = config.get_int("memory") or 512

# Use in resources
service = aws.ecs.Service(
    "api-service",
    cluster=cluster.arn,
    desired_count=config.get_int("desiredCount") or 2,
    task_definition=task_def.arn,
    # ...
)
```

## Docker Configuration

### docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: modules/api/Dockerfile
      args:
        PYTHON_VERSION: ${PYTHON_VERSION:-3.12}
    image: pantstack/api:local
    container_name: pantstack_api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    volumes:
      - ./modules/api:/app
    depends_on:
      - postgres
      - redis
    networks:
      - pantstack
    restart: unless-stopped

  admin:
    build:
      context: .
      dockerfile: modules/admin/Dockerfile
    image: pantstack/admin:local
    container_name: pantstack_admin
    ports:
      - "8001:8000"
    environment:
      - API_URL=http://api:8000
      - DATABASE_URL=${DATABASE_URL}
    networks:
      - pantstack
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    container_name: pantstack_postgres
    environment:
      - POSTGRES_DB=pantstack
      - POSTGRES_USER=pantstack
      - POSTGRES_PASSWORD=pantstack
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - pantstack
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: pantstack_redis
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    networks:
      - pantstack
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:

networks:
  pantstack:
    driver: bridge
```

### Dockerfile

```dockerfile
# modules/api/Dockerfile
ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install dependencies
COPY 3rdparty/python/requirements-api-api.txt .
RUN pip install --no-cache-dir -r requirements-api-api.txt

# Copy application code
COPY modules/api/backend /app/backend

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## GitHub Actions Configuration

### Workflow Environment Variables

```yaml
# .github/workflows/ci.yml
env:
  PYTHON_VERSION: '3.12'
  PANTS_VERSION: '2.28.0'
  AWS_REGION: us-east-1
  ECR_REGISTRY: ${{ secrets.ECR_REGISTRY }}
  ECR_REPOSITORY: ${{ secrets.ECR_REPOSITORY }}
  PULUMI_ACCESS_TOKEN: ${{ secrets.PULUMI_ACCESS_TOKEN }}
```

### Repository Secrets

Required GitHub repository secrets:
```
AWS_ACCOUNT_ID          # AWS account ID
AWS_REGION             # AWS region
ECR_REGISTRY           # ECR registry URL
ECR_REPOSITORY         # ECR repository name
PULUMI_ACCESS_TOKEN    # Pulumi Cloud token
GITHUB_TOKEN           # Auto-provided by GitHub
```

## Python Package Configuration

### pyproject.toml

```toml
[tool.black]
line-length = 88
target-version = ['py312']
include = '\.pyi?$'
extend-exclude = '''
/(
    \.git
  | \.pants\.d
  | dist
  | build
)/
'''

[tool.isort]
profile = "black"
line_length = 88
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true

[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
ignore_missing_imports = true

[tool.pytest.ini_options]
minversion = "7.0"
testpaths = ["tests", "backend/tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
addopts = "-ra -q --strict-markers"
markers = [
    "slow: marks tests as slow",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
]

[tool.coverage.run]
source = ["backend"]
omit = ["*/tests/*", "*/__init__.py"]

[tool.coverage.report]
precision = 2
show_missing = true
skip_covered = false
```

### .flake8

```ini
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude =
    .git,
    __pycache__,
    .pants.d,
    dist,
    build,
    *.egg-info
per-file-ignores =
    __init__.py:F401
```

## Makefile Configuration

Key variables in Makefile:
```makefile
# Python version
PYTHON_VERSION := 3.12

# Pants configuration
PANTS_VERSION := 2.28.0
PANTS := pants

# Docker configuration
DOCKER_COMPOSE := docker-compose
DOCKER_BUILD_ARGS := --build-arg PYTHON_VERSION=$(PYTHON_VERSION)

# Module defaults
DEFAULT_MODULE := api
DEFAULT_ENV := test

# Paths
MODULES_DIR := modules
STACK_DIR := stack
LOCKFILES_DIR := lockfiles
```

## Logging Configuration

```python
# logging_config.py
import logging.config

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "json": {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "json",
            "filename": "app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"],
    },
    "loggers": {
        "uvicorn": {
            "level": "INFO",
        },
        "sqlalchemy": {
            "level": "WARNING",
        },
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
```
