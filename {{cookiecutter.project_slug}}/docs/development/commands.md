# Development Commands

Quick reference for all Pantstack development commands.

## Setup Commands

### Initial Setup
```bash
# Install Pants build system
make boot

# Add to PATH
export PATH="$HOME/.local/bin:$PATH"

# Copy and configure environment
cp .env.example .env
# Edit .env with your values

# Bootstrap infrastructure
make bootstrap
```

## Development Workflow

### Code Quality
```bash
# Format code
make fmt

# Run linters
make lint

# Type checking
make typecheck

# Run all checks
make check
```

### Testing
```bash
# Run all tests
make test

# Test specific module
make test M=api

# Test with coverage
pants test --use-coverage ::

# Test specific file
pants test modules/api/backend/tests/test_main.py
```

### Building
```bash
# Build all modules
make build

# Build specific module
make build M=api

# Package module (test + build)
make mod M=api

# Build Docker images
pants package ::
```

## Module Management

### Create New Module
```bash
# Create module locally
make new-module M=orders

# Create module with GitHub PR
make gh-new-module-pr M=orders
```

### Module Operations
```bash
# Test and package module
make mod M=api

# List module dependencies
pants dependencies modules/api::

# Show module graph
pants peek modules/api::
```

## Local Development

### Docker Compose
```bash
# Start local services
make up

# Stop services
make down

# View logs
docker-compose logs -f api

# Rebuild and restart
make down build up
```

### Local Testing
```bash
# Run service locally
cd modules/api
python -m backend.api.main

# Run with hot reload
uvicorn backend.api.main:app --reload --port 8000

# Test endpoints
curl http://localhost:8000/health
```

## Dependency Management

### Update Dependencies
```bash
# Add dependency to module
echo "fastapi==0.104.1" >> 3rdparty/python/requirements-api-api.txt

# Generate lockfiles
make locks

# Update specific lockfile
pants generate-lockfiles --resolve=api_api
```

### View Dependencies
```bash
# Show module dependencies
pants dependencies modules/api::

# Show reverse dependencies
pants dependents modules/shared/backend/public::

# Check for conflicts
pants validate ::
```

## Infrastructure Commands

### Pulumi Stack Management
```bash
# Initialize stacks for all modules
make seed-stacks

# Deploy to test environment
make stack-up M=api ENV=test

# Preview changes
make stack-preview M=api ENV=test

# Destroy stack
make stack-down M=api ENV=test

# Verify deployment
make stack-verify M=api ENV=test
```

### Direct Pulumi Commands
```bash
# Select stack
cd modules/api/infrastructure
pulumi stack select test

# Show current state
pulumi stack

# Refresh state
pulumi refresh

# Show outputs
pulumi stack output
```

## CI/CD Commands

### GitHub Actions
```bash
# Trigger deployment
make gha-deploy M=api ENV=prod

# Create release PR
gh pr create --base main --head dev \
  --title "Release v1.2.0" \
  --label "release:minor"

# View workflow runs
gh run list --workflow=ci.yml

# Watch workflow
gh run watch
```

### Version Management
```bash
# View current version
git describe --tags --abbrev=0

# Create manual release
git tag -a v1.2.3 -m "Release v1.2.3"
git push origin v1.2.3
```

## Template Commands

### Template Publishing
```bash
# Initialize as template (first time)
make init-template

# Update template
make publish-template

# Show template help
make template-help
```

### Project Creation
```bash
# Interactive creation wizard
make quickstart

# Create from local template
make new-project

# Create from remote template
cruft create gh:MehdiZare/pantstack
```

## Debugging Commands

### Pants Debugging
```bash
# Run with debug output
pants --no-pantsd test :: -ldebug

# Show Pants configuration
pants help-all

# Clear Pants cache
rm -rf ~/.cache/pants

# Show build graph
pants peek ::
```

### Docker Debugging
```bash
# Shell into container
docker exec -it pantstack_api_1 /bin/bash

# View container logs
docker logs pantstack_api_1 --tail 100 -f

# Inspect image
docker inspect pantstack/api:latest

# Clean Docker resources
docker system prune -a
```

### AWS Debugging
```bash
# Check AWS credentials
aws sts get-caller-identity

# List ECR images
aws ecr list-images --repository-name pantstack

# View ECS service
aws ecs describe-services \
  --cluster api-cluster \
  --services api-service

# Tail CloudWatch logs
aws logs tail /ecs/api --follow
```

## Utility Commands

### Environment Variables
```bash
# Load .env file
export $(cat .env | xargs)

# Check environment
env | grep PANTSTACK

# Validate configuration
make validate-env
```

### Git Operations
```bash
# Sync with upstream
git fetch upstream
git checkout main
git merge upstream/main

# Clean branches
git branch --merged | grep -v main | xargs git branch -d

# Reset to remote
git fetch origin
git reset --hard origin/dev
```

## Makefile Targets Reference

| Target | Description |
|--------|-------------|
| `boot` | Install Pants build system |
| `fmt` | Format all code |
| `lint` | Run linters |
| `test` | Run all tests |
| `build` | Build all modules |
| `mod M=name` | Test and package specific module |
| `locks` | Generate dependency lockfiles |
| `up` | Start local services |
| `down` | Stop local services |
| `new-module M=name` | Create new module |
| `bootstrap` | Bootstrap infrastructure |
| `seed-stacks` | Initialize Pulumi stacks |
| `stack-up M=name ENV=env` | Deploy stack |
| `stack-preview M=name ENV=env` | Preview deployment |
| `gha-deploy M=name ENV=env` | Trigger GitHub deployment |

## Environment-Specific Commands

### Development Environment
```bash
# Deploy all to test
make deploy-all ENV=test

# Run integration tests
make integration-test ENV=test
```

### Production Environment
```bash
# Preview production changes
make stack-preview M=api ENV=prod

# Deploy with approval
make stack-up M=api ENV=prod --require-approval

# Monitor deployment
make monitor M=api ENV=prod
```
