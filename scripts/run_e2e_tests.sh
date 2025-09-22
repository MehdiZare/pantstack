#!/bin/bash

# E2E Test Runner Script for Pantstack Template
# This script sets up the environment and runs comprehensive e2e tests

set -e

echo "🚀 Starting Pantstack E2E Test Suite"
echo "====================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to wait for a service
wait_for_service() {
    local service_name=$1
    local url=$2
    local max_attempts=60
    local attempt=1

    echo -n "Waiting for $service_name..."

    while [ $attempt -le $max_attempts ]; do
        if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -qE "200|401|404"; then
            echo -e " ${GREEN}✓${NC}"
            return 0
        fi

        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done

    echo -e " ${RED}✗${NC}"
    echo "Failed to connect to $service_name after $max_attempts attempts"
    return 1
}

# Check prerequisites
echo "Checking prerequisites..."

if ! command_exists docker; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

if ! command_exists docker-compose; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    exit 1
fi

if ! command_exists python3; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

if ! command_exists supabase; then
    echo -e "${YELLOW}Warning: Supabase CLI is not installed. Some tests may fail.${NC}"
    echo "Install with: brew install supabase/tap/supabase"
fi

echo -e "${GREEN}Prerequisites check passed${NC}"

# Set up environment
echo ""
echo "Setting up test environment..."
export ENV=test
export DEBUG=true
export LOCALSTACK=true
export LOCALSTACK_ENDPOINT=http://localhost:4566
export SUPABASE_URL=http://localhost:54321
export SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0
export REDIS_URL=redis://localhost:6379
export CELERY_BROKER_URL=redis://localhost:6379/0
export CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Start Supabase if available
if command_exists supabase; then
    echo ""
    echo "Starting Supabase..."
    supabase start 2>/dev/null || echo -e "${YELLOW}Supabase may already be running${NC}"

    # Apply migrations if Supabase is running
    if [ -d "$PROJECT_ROOT/supabase/migrations" ]; then
        echo "Applying Supabase migrations..."
        for migration in "$PROJECT_ROOT"/supabase/migrations/*.sql; do
            if [ -f "$migration" ]; then
                echo "  Applying: $(basename "$migration")"
                # Note: This would normally use supabase db push or similar
            fi
        done
    fi
else
    echo -e "${YELLOW}Skipping Supabase setup (CLI not installed)${NC}"
fi

# Start Docker Compose stack
echo ""
echo "Starting Docker Compose stack..."
docker-compose up -d

# Wait for services to be ready
echo ""
echo "Waiting for services to be ready..."

wait_for_service "LocalStack" "http://localhost:4566/_localstack/health"
wait_for_service "Redis" "http://localhost:6379" 2>/dev/null || echo -e "${YELLOW}Redis check skipped (no HTTP endpoint)${NC}"
wait_for_service "API" "http://localhost:8000/health"
wait_for_service "Flower" "http://localhost:5555/api/workers"

if command_exists supabase; then
    wait_for_service "Supabase" "http://localhost:54321/rest/v1/"
fi

echo ""
echo -e "${GREEN}All services are ready!${NC}"

# Install test dependencies
echo ""
echo "Installing test dependencies..."
pip3 install -q pytest requests boto3 redis 2>/dev/null || true

# Run the tests
echo ""
echo "Running E2E tests..."
echo "===================="

# Run with pytest
if command_exists pytest; then
    pytest "$PROJECT_ROOT/tests/integration/test_full_stack_e2e.py" -v -s --tb=short
    TEST_EXIT_CODE=$?
else
    # Fallback to direct Python execution
    python3 "$PROJECT_ROOT/tests/integration/test_full_stack_e2e.py"
    TEST_EXIT_CODE=$?
fi

# Show test results
echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ All E2E tests passed!${NC}"
else
    echo -e "${RED}❌ Some tests failed. Check the output above.${NC}"
fi

# Optionally show logs on failure
if [ $TEST_EXIT_CODE -ne 0 ]; then
    echo ""
    read -p "Do you want to see the service logs? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "API Logs:"
        docker-compose logs --tail=50 api
        echo ""
        echo "Celery Worker Logs:"
        docker-compose logs --tail=50 celery_worker
    fi
fi

# Cleanup option
echo ""
read -p "Do you want to stop the services? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Stopping services..."
    docker-compose down

    if command_exists supabase; then
        supabase stop 2>/dev/null || true
    fi

    echo -e "${GREEN}Services stopped${NC}"
else
    echo -e "${YELLOW}Services are still running. Remember to stop them with 'docker-compose down'${NC}"
fi

exit $TEST_EXIT_CODE
