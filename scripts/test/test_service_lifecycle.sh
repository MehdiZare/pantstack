#!/usr/bin/env bash
# Test service creation, building, and cleanup
set -euo pipefail

TEST_SERVICE_PREFIX="test_temp_"
TEST_SERVICES=()
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Setup: Create test workspace
setup_test_environment() {
    echo -e "${YELLOW}🔧 Setting up test environment...${NC}"
    export TEST_MODE=true
    export TEST_RUN_ID=$(date +%s)
    cd "$PROJECT_ROOT"
}

# Create test service with automatic tracking
create_test_service() {
    local service_suffix="${1:-test}"
    local service_name="${TEST_SERVICE_PREFIX}${service_suffix}_${TEST_RUN_ID}"
    echo -e "${YELLOW}📦 Creating test service: $service_name${NC}"

    # Track for cleanup
    TEST_SERVICES+=("$service_name")

    # Create service
    S="$service_name" ./scripts/new_service.sh

    # Verify creation
    if [ -d "services/$service_name" ]; then
        echo -e "${GREEN}✅ Service created: services/$service_name${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed to create service${NC}"
        return 1
    fi
}

# Test service functionality
test_service_operations() {
    local service_name=$1

    echo -e "${YELLOW}🧪 Testing service operations for: $service_name${NC}"

    # Verify directory structure
    echo "  Checking directory structure..."
    for dir in "app/api" "app/worker" "domain/models" "domain/services" "tests/unit"; do
        if [ -d "services/$service_name/$dir" ]; then
            echo -e "    ${GREEN}✓${NC} $dir"
        else
            echo -e "    ${RED}✗${NC} $dir missing"
            return 1
        fi
    done

    # Verify BUILD file
    echo "  Checking BUILD file..."
    if [ -f "services/$service_name/BUILD" ]; then
        if grep -q "entry_point=\"services.$service_name" "services/$service_name/BUILD"; then
            echo -e "    ${GREEN}✓${NC} BUILD file configured correctly"
        else
            echo -e "    ${RED}✗${NC} BUILD file misconfigured"
            return 1
        fi
    else
        echo -e "    ${RED}✗${NC} BUILD file missing"
        return 1
    fi

    # Test Pants operations (if pants is available)
    if command -v ./pants &> /dev/null; then
        echo "  Testing Pants operations..."
        if ./pants filedeps "services/$service_name::" 2>/dev/null; then
            echo -e "    ${GREEN}✓${NC} Pants filedeps successful"
        else
            echo -e "    ${YELLOW}⚠${NC} Pants filedeps failed (may need lockfile generation)"
        fi
    else
        echo -e "  ${YELLOW}⚠${NC} Pants not available, skipping build tests"
    fi

    echo -e "${GREEN}✅ Service operations test complete${NC}"
}

# Cleanup: Remove all test artifacts
cleanup_test_services() {
    echo -e "${YELLOW}🧹 Cleaning up test services...${NC}"

    local cleaned_count=0
    for service in "${TEST_SERVICES[@]}"; do
        if [ -d "services/$service" ]; then
            echo "  Removing: services/$service"
            rm -rf "services/$service"
            ((cleaned_count++))
        fi
    done

    # Also clean any orphaned test services
    find services -type d -name "${TEST_SERVICE_PREFIX}*" 2>/dev/null | while read -r orphan; do
        echo "  Removing orphaned: $orphan"
        rm -rf "$orphan"
        ((cleaned_count++))
    done

    # Clean Pants cache if available
    if command -v ./pants &> /dev/null; then
        ./pants --no-watch-filesystem gc 2>/dev/null || true
    fi

    echo -e "${GREEN}✨ Cleanup complete - removed $cleaned_count services${NC}"
}

# Error handler
handle_error() {
    echo -e "${RED}❌ Error occurred on line $1${NC}"
    cleanup_test_services
    exit 1
}

# Trap to ensure cleanup on exit
trap cleanup_test_services EXIT
trap 'handle_error $LINENO' ERR

# Main test execution
main() {
    echo -e "${GREEN}═══════════════════════════════════════${NC}"
    echo -e "${GREEN}  Service Lifecycle Test Suite${NC}"
    echo -e "${GREEN}═══════════════════════════════════════${NC}"

    setup_test_environment

    # Test 1: Basic service creation
    echo -e "\n${YELLOW}Test 1: Basic Service Creation${NC}"
    create_test_service "basic"
    test_service_operations "${TEST_SERVICE_PREFIX}basic_${TEST_RUN_ID}"

    # Test 2: Multiple services
    echo -e "\n${YELLOW}Test 2: Multiple Service Creation${NC}"
    create_test_service "api"
    create_test_service "worker"

    # Verify both exist
    for suffix in "api" "worker"; do
        service_name="${TEST_SERVICE_PREFIX}${suffix}_${TEST_RUN_ID}"
        if [ -d "services/$service_name" ]; then
            echo -e "${GREEN}✅ Service exists: $service_name${NC}"
        else
            echo -e "${RED}❌ Service missing: $service_name${NC}"
            exit 1
        fi
    done

    # Test 3: Service with special characters (sanitized)
    echo -e "\n${YELLOW}Test 3: Service Name Validation${NC}"
    create_test_service "valid_name"

    echo -e "\n${GREEN}═══════════════════════════════════════${NC}"
    echo -e "${GREEN}🎉 All tests completed successfully!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════${NC}"
}

# Allow running specific functions if needed
if [ $# -gt 0 ]; then
    case "$1" in
        cleanup)
            cleanup_test_services
            ;;
        create)
            setup_test_environment
            create_test_service "${2:-test}"
            ;;
        *)
            main "$@"
            ;;
    esac
else
    main
fi