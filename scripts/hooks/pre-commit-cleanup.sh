#!/usr/bin/env bash
# Pre-commit hook to prevent committing test services
set -euo pipefail

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Find test services
test_services=$(find services -type d \( -name "test_*" -o -name "temp_*" -o -name "test_temp_*" \) 2>/dev/null || true)

if [ -n "$test_services" ]; then
    echo -e "${RED}⚠️  Found test services that should not be committed:${NC}"
    echo "$test_services" | while read -r service; do
        echo -e "  ${YELLOW}• $service${NC}"
    done
    echo ""
    echo -e "${YELLOW}Run one of these commands to clean them:${NC}"
    echo -e "  ${GREEN}make clean-test-services${NC}     # Remove all test services"
    echo -e "  ${GREEN}./scripts/test/test_service_lifecycle.sh cleanup${NC}  # Alternative cleanup"
    echo ""
    echo -e "${RED}Commit aborted. Please clean test services and try again.${NC}"
    exit 1
fi

# Also check for test artifacts in BUILD files
test_build_files=$(grep -r "test_temp_\|test_svc_" services/*/BUILD 2>/dev/null || true)

if [ -n "$test_build_files" ]; then
    echo -e "${RED}⚠️  Found test references in BUILD files:${NC}"
    echo "$test_build_files"
    echo ""
    echo -e "${YELLOW}These may be leftover from incomplete cleanup.${NC}"
    echo -e "${YELLOW}Please review and clean these references.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ No test services found - OK to commit${NC}"