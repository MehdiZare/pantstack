# Local Development Setup Guide

## Prerequisites

- Docker and Docker Compose installed
- Python 3.11 or higher
- Make installed
- Pants build system (installed via `make boot`)

## Initial Setup

1. **Install Pants Build System**
   ```bash
   make boot
   # Add to PATH if not already done:
   export PATH="$HOME/.local/bin:$PATH"
   ```

2. **Copy Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your specific values if needed
   ```

## Starting the Local Development Stack

### 1. Start Infrastructure Services

The local stack includes:
- **API Service**: Main FastAPI application (port 8000)
- **Redis**: Cache and message broker (port 6379)
- **LocalStack**: AWS service emulation (port 4566)
- **Supabase**: Database and authentication (port 54321)
- **Flower**: Celery monitoring UI (port 5555)

```bash
# Start all services
make up

# Or use docker-compose directly
docker compose up -d
```

### 2. Verify Services Health

Check that all services are running:

```bash
# Check Docker containers
docker ps

# Verify API health
curl http://localhost:8000/
# Expected: {"message":"Pantstack API - Entry Point"}

# Check LocalStack status
curl http://localhost:4566/_localstack/health | jq
# Should show various AWS services as "available"

# Check Supabase
curl -I http://localhost:54321/rest/v1/
# Expected: HTTP 200 OK
```

## Running Integration Tests

Integration tests verify the complete system functionality:

```bash
# Run all integration tests
./pants test tests/integration:: --tag=integration --no-test-use-coverage

# Run specific test suites
./pants test tests/integration:test_localstack_services --no-test-use-coverage
./pants test tests/integration:test_docker_compose --no-test-use-coverage
./pants test tests/integration:test_supabase_integration --no-test-use-coverage
```

### Test Coverage

- **LocalStack Tests**: Verify AWS service emulation (S3, SQS, DynamoDB, etc.)
- **Docker Compose Tests**: Ensure all containers are healthy and communicating
- **Supabase Tests**: Database operations and authentication
- **End-to-End Tests**: Complete workflow validation

## Troubleshooting

### Common Issues and Solutions

1. **Pydantic Import Errors**
   - The codebase uses Pydantic v2 which moved `BaseSettings` to `pydantic-settings`
   - If you encounter import errors, ensure `pydantic-settings` is in requirements

2. **Service Connection Failures**
   - Ensure no other services are using required ports (8000, 6379, 4566, 54321)
   - Check Docker logs: `docker compose logs [service_name]`

3. **Celery Worker Issues**
   - Workers may fail with configuration errors
   - Workaround: Main API functionality works without workers for local development
   - To debug: `docker compose logs celery_worker`

4. **Test Failures**
   - Some tests may fail in sandboxed environments
   - Use `--no-test-use-sandbox` flag for CLI and lifecycle tests if needed

### Useful Commands

```bash
# View logs for a specific service
docker compose logs -f api

# Restart a specific service
docker compose restart api

# Stop all services
make down
# or
docker compose down

# Clean rebuild (removes volumes)
docker compose down -v
make up

# Check Pants configuration
./pants version
./pants roots

# Format and lint code
make fmt
make lint
```

## Development Workflow

1. **Start services**: `make up`
2. **Make code changes** in your editor
3. **Services auto-reload** on code changes (FastAPI dev mode)
4. **Run tests**: `./pants test services/[service_name]::`
5. **Check logs** if issues occur: `docker compose logs -f [service_name]`

## Service Endpoints

- **API**: http://localhost:8000
  - Docs: http://localhost:8000/docs
  - OpenAPI: http://localhost:8000/openapi.json
- **LocalStack**: http://localhost:4566
- **Supabase Studio**: http://localhost:54323
- **Flower (Celery UI)**: http://localhost:5555
- **Redis**: localhost:6379

## Environment Variables

Key environment variables for local development:

- `ENVIRONMENT=development` - Sets development mode
- `DEBUG=true` - Enables debug logging
- `LOG_LEVEL=INFO` - Logging verbosity
- `AWS_LOCALSTACK_ENABLED=true` - Use LocalStack instead of real AWS
- `SUPABASE_URL` - Supabase connection URL
- `REDIS_HOST=redis` - Redis connection

See `.env.example` for complete list.

## Next Steps

- Explore service APIs at http://localhost:8000/docs
- Create a new service: `make new-service S=your_service_name`
- Run unit tests: `./pants test services::`
- Deploy to test environment: `make stack-up S=api ENV=test`