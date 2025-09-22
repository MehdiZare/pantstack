# E2E Testing for Pantstack Template

This document describes the comprehensive end-to-end testing implementation for the Pantstack template, which validates the full functionality including API endpoints, Celery tasks, and Supabase integration.

## Overview

The E2E test suite validates that the entire Pantstack template works correctly when deployed, ensuring all components integrate properly:
- API service discovery and routing
- Celery task execution via workers
- Data persistence in Supabase
- AWS services via LocalStack
- Redis for caching and task queues

## Test Structure

### Core Test Files

1. **`tests/integration/test_full_stack_e2e.py`**
   - Comprehensive E2E test suite
   - Tests full workflow from API → Celery → Database
   - Validates service health and integration
   - Includes stress testing with concurrent tasks

2. **`tests/integration/helpers.py`**
   - Docker Compose management utilities
   - Service health checking
   - Supabase and LocalStack test helpers
   - Test environment setup utilities

### Service Components

1. **Auth Service Tasks** (`services/auth/app/tasks.py`)
   - User registration processing
   - Email verification
   - API key rotation
   - User activity auditing
   - Permission synchronization

2. **Agent Service Tasks** (`services/agent/app/tasks.py`)
   - Data processing
   - Workflow execution
   - Report generation
   - External data synchronization
   - Batch processing
   - Health checks

3. **API Enhancements** (`services/agent/app/api/main.py`)
   - Celery integration for task submission
   - Task status tracking via Celery
   - Fallback to background tasks when Celery unavailable

### Database Schema

**Supabase Tables** (`supabase/migrations/001_create_task_tables.sql`):
- `e2e_test_results` - Stores test task results
- `task_status` - Tracks task execution status
- `celery_task_results` - Celery-specific task results
- `task_audit_log` - Audit trail for task operations
- `task_summary` - View for task analytics

## Running the Tests

### Quick Start

```bash
# Run the automated test script
./scripts/run_e2e_tests.sh
```

### Manual Testing

1. **Start Services:**
```bash
# Start Supabase (if installed)
supabase start

# Start Docker Compose stack
docker-compose up -d

# Wait for services to be ready
sleep 30
```

2. **Run Tests:**
```bash
# Set environment variables
export ENV=test
export LOCALSTACK=true
export SUPABASE_URL=http://localhost:54321

# Run with pytest
pytest tests/integration/test_full_stack_e2e.py -v -s

# Or run specific test
pytest tests/integration/test_full_stack_e2e.py::TestFullStackE2E::test_02_create_async_task_via_api -v
```

3. **Check Results:**
```bash
# View Celery tasks in Flower
open http://localhost:5555

# Check API health
curl http://localhost:8000/health

# View service logs
docker-compose logs -f api celery_worker
```

## Test Coverage

The E2E tests validate:

### 1. Service Initialization
- All Docker services start correctly
- Health endpoints respond
- Service discovery works

### 2. API Functionality
- Health check endpoint
- Service discovery endpoint
- Task creation endpoint
- Task status retrieval
- Task listing and filtering

### 3. Celery Task Execution
- Tasks are submitted to Celery queues
- Workers process tasks successfully
- Results are stored and retrievable
- Task status updates correctly

### 4. Data Persistence
- Supabase tables are created
- Task results are stored
- Audit logs are maintained
- Data can be queried and retrieved

### 5. AWS Services (LocalStack)
- S3 bucket operations
- SQS message queuing
- File storage and retrieval

### 6. Stress Testing
- Concurrent task submission
- System stability under load
- Resource cleanup

## Test Workflow Example

The tests simulate a complete user workflow:

1. **Submit Task via API**
   ```python
   POST /agent/tasks
   {
       "name": "process_data",
       "task_type": "data_processing",
       "payload": {...}
   }
   ```

2. **Task Processed by Celery**
   - Task queued in Redis
   - Worker picks up task
   - Processing executed
   - Result generated

3. **Result Stored in Database**
   - Task status updated
   - Result stored in Supabase
   - Audit log created

4. **Result Retrieved via API**
   ```python
   GET /agent/tasks/{task_id}
   ```

## Monitoring and Debugging

### View Celery Tasks
- Flower UI: http://localhost:5555
- Shows active workers
- Task history and results
- Queue statistics

### Check Service Logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs celery_worker

# Follow logs
docker-compose logs -f api
```

### Database Inspection
```bash
# Connect to Supabase Studio
open http://localhost:54323

# View task results table
# Check audit logs
# Monitor task status
```

## Troubleshooting

### Common Issues

1. **Services not starting:**
   - Check Docker is running
   - Verify ports are available
   - Review docker-compose logs

2. **Celery tasks not executing:**
   - Verify Redis is running
   - Check worker logs
   - Ensure tasks are registered

3. **Database connection issues:**
   - Verify Supabase is running
   - Check authentication keys
   - Review migration status

4. **Test failures:**
   - Check service health endpoints
   - Review specific test output
   - Inspect service logs

### Cleanup

```bash
# Stop all services
docker-compose down

# Stop Supabase
supabase stop

# Remove test data
docker volume prune
```

## CI/CD Integration

To run these tests in CI/CD:

```yaml
# GitHub Actions example
- name: Start services
  run: docker-compose up -d

- name: Wait for services
  run: sleep 30

- name: Run E2E tests
  run: pytest tests/integration/test_full_stack_e2e.py

- name: Stop services
  if: always()
  run: docker-compose down
```

## Extending the Tests

To add new test cases:

1. Add new test methods to `TestFullStackE2E`
2. Create new task types in service task files
3. Add corresponding API endpoints
4. Update database schema if needed
5. Add test helpers to `helpers.py`

## Summary

This E2E test implementation provides comprehensive validation of the Pantstack template, ensuring all components work together correctly. The tests can be run locally or in CI/CD pipelines, providing confidence that the template functions properly when deployed.
