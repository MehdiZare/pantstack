# CLI Commands Reference

This document provides a comprehensive reference for all CLI commands available in the Pantstack monorepo.

## Table of Contents

- [Setup Commands](#setup-commands)
- [Template Commands](#template-commands)
- [Development Commands](#development-commands)
- [Service Management](#service-management)
- [Infrastructure Commands](#infrastructure-commands)
- [Testing Commands](#testing-commands)
- [GitHub/CI Commands](#githubci-commands)

## Setup Commands

### `make setup`
Complete development environment setup with interactive prompts.

```bash
make setup
```

This command will:
- Check for required tools
- Install missing dependencies
- Configure your environment
- Set up pre-commit hooks

### `make setup-quick`
Quick setup without prompts (suitable for CI/CD).

```bash
make setup-quick
```

### `make check-tools`
Verify all required tools are installed.

```bash
make check-tools
```

Required tools:
- Python 3.11+
- Docker & Docker Compose
- Pants build system
- Git
- Make

## Template Commands

### `make quickstart`
Interactive setup wizard for creating new projects from this template.

```bash
make quickstart
```

### `make new-project`
Create a new project from this template using Cruft.

```bash
make new-project
```

You'll be prompted for:
- Project name
- AWS account ID
- GitHub organization
- Other configuration values

### `make init-template`
Initialize and publish this repository as a reusable template.

```bash
make init-template
```

**Prerequisites:**
- `.env` file with GitHub credentials
- GitHub CLI authenticated

### `make template-help`
Show detailed template usage guide.

```bash
make template-help
```

## Development Commands

### Starting Services

#### `make dev-up`
Start minimal development stack (Redis, LocalStack).

```bash
make dev-up
# Then run separately:
supabase start
```

#### `make dev-down`
Stop development services.

```bash
make dev-down
```

#### `make up`
Start full local stack with all services.

```bash
make up
```

Services available at:
- API: http://localhost:8000
- Flower: http://localhost:5555
- LocalStack: http://localhost:4566

#### `make down`
Stop and clean up all services.

```bash
make down
```

### Code Quality

#### `make fmt`
Format all code using Black and isort.

```bash
make fmt
```

#### `make lint`
Run linting and type checking.

```bash
make lint
```

#### `make pre-commit-install`
Install pre-commit hooks for automatic code quality checks.

```bash
make pre-commit-install
```

### Building

#### `make package`
Build Docker images for all services.

```bash
make package
```

#### `make locks`
Generate/update Pants lockfiles for dependencies.

```bash
make locks
```

## Service Management

### `make new-service`
Scaffold a new microservice with standard structure.

```bash
make new-service S=orders
```

Creates:
- Service directory structure
- API and worker templates
- Domain models
- BUILD file
- Infrastructure configuration
- Test structure

### Enhanced Service Creation

For a more comprehensive service with all features:

```bash
./scripts/new_service_enhanced.sh
# or
S=orders ./scripts/new_service_enhanced.sh
```

This creates a service with:
- Full CRUD API with FastAPI
- Supabase database integration
- Celery task support
- SQS/EventBridge handlers
- Domain-Driven Design structure
- Complete test suite
- Docker containers
- Infrastructure as Code

### `make mod-s`
Test and package a specific service.

```bash
make mod-s S=web
```

This runs:
1. Service tests
2. Docker image build

### `make gh-new-service-pr`
Create a new service and open a PR.

```bash
make gh-new-service-pr S=orders
```

This will:
1. Create a new branch
2. Scaffold the service
3. Commit changes
4. Push to GitHub
5. Open a pull request

## Infrastructure Commands

### Stack Management

#### `make bootstrap`
Bootstrap foundation infrastructure (first-time setup).

```bash
make bootstrap
```

**Prerequisites:**
- Filled `.env` file
- AWS credentials configured
- Pulumi account

#### `make seed-stacks`
Initialize Pulumi stacks for all services.

```bash
make seed-stacks
```

#### `make svc-stack-up`
Deploy a service stack.

```bash
make svc-stack-up S=web ENV=test
```

Parameters:
- `S`: Service name
- `ENV`: Environment (test/prod)

#### `make svc-stack-preview`
Preview infrastructure changes before deployment.

```bash
make svc-stack-preview S=web ENV=prod
```

#### `make svc-stack-outputs`
Show stack outputs (URLs, resource IDs).

```bash
make svc-stack-outputs S=web ENV=test
```

### LocalStack Commands

#### `make localstack-up`
Start LocalStack with initialization.

```bash
make localstack-up
```

#### `make ls-tables`
List DynamoDB tables in LocalStack.

```bash
make ls-tables
```

#### `make ls-queues`
List SQS queues in LocalStack.

```bash
make ls-queues
```

#### `make ls-buckets`
List S3 buckets in LocalStack.

```bash
make ls-buckets
```

## Testing Commands

### `make test`
Run all tests.

```bash
make test
```

### `make test-unit`
Run unit tests only.

```bash
make test-unit
```

### `make test-integration`
Run integration tests (requires `dev-up`).

```bash
make test-integration
```

### `make test-service`
Test a specific service.

```bash
make test-service S=auth
```

### `make test-coverage`
Generate test coverage report.

```bash
make test-coverage
```

### Test Cleanup

#### `make clean-test-services`
Clean up any leftover test services.

```bash
make clean-test-services
```

#### `make check-test-artifacts`
Check for any test artifacts left behind.

```bash
make check-test-artifacts
```

## GitHub/CI Commands

### `make gha-ci`
Trigger CI workflow manually.

```bash
make gha-ci
```

### `make gha-deploy`
Trigger deployment workflow.

```bash
make gha-deploy M=api ENV=prod
```

Parameters:
- `M`: Module/service name
- `ENV`: Target environment

### `make gh-new-branch`
Create a new Git branch.

```bash
make gh-new-branch B=feature/new-feature
```

### `make gh-open-pr`
Open a pull request.

```bash
make gh-open-pr B=feature/new-feature BASE=dev TITLE="Add new feature"
```

## Environment Variables

Key environment variables used by commands:

```bash
# AWS Configuration
AWS_ACCOUNT_ID=123456789012
AWS_REGION=us-east-1

# GitHub Configuration
GITHUB_OWNER=your-org
GITHUB_REPO=your-repo

# Pulumi Configuration
PULUMI_ORG=your-pulumi-org

# Supabase Configuration
SUPABASE_URL=http://localhost:54321
SUPABASE_ANON_KEY=your-anon-key

# Service Configuration
ENV=development  # or test, prod
DEBUG=true
LOCALSTACK=true  # Use LocalStack instead of AWS
```

## Troubleshooting

### Common Issues

#### "No rule to make target"
The command doesn't exist. Run `make help` to see available commands.

#### "command not found: pants"
Run `make boot` to install Pants build system.

#### Docker permission errors
Ensure Docker daemon is running and you have permissions:
```bash
docker ps  # Should list containers
```

#### LocalStack not starting
Check if ports are already in use:
```bash
lsof -i :4566  # Check LocalStack port
```

#### Service creation fails
Ensure you have write permissions and the service doesn't already exist:
```bash
ls services/  # Check existing services
```

### Getting Help

1. Run `make help` for command list
2. Check script help: `./scripts/script-name.sh --help`
3. Review logs: `docker-compose logs service-name`
4. Check GitHub Issues for known problems

## Best Practices

1. **Always run tests before committing:**
   ```bash
   make test-unit
   ```

2. **Format code before pushing:**
   ```bash
   make fmt
   ```

3. **Use development environment for testing:**
   ```bash
   make dev-up
   # Test your changes
   make dev-down
   ```

4. **Clean up test artifacts:**
   ```bash
   make clean-test-services
   ```

5. **Verify infrastructure changes:**
   ```bash
   make svc-stack-preview S=service ENV=test
   ```

## Script Locations

All scripts are located in the `scripts/` directory:

- `new_service.sh` - Basic service scaffolding
- `new_service_enhanced.sh` - Enhanced service with all features
- `bootstrap_foundation.sh` - Infrastructure bootstrap
- `quickstart.sh` - Interactive setup wizard
- `setup-tools.sh` - Development tools installation
- `update_pants_resolvers.sh` - Update Pants configuration
- `test/` - Testing scripts
- `setup/` - Setup and verification scripts

## Contributing

When adding new commands:

1. Add to `Makefile` with clear target name
2. Include help text: `target: ## Description`
3. Add to `.PHONY` if not creating files
4. Document in this file
5. Add tests in `cli/tests/`

Example:
```makefile
.PHONY: new-command

new-command: ## Description of what it does
	@echo "Executing new command..."
	./scripts/new-command.sh
```
