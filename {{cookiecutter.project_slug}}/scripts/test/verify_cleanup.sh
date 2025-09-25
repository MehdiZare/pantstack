#!/usr/bin/env bash
# Verify that no test artifacts remain after testing
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test resource prefixes
TEST_PREFIXES=("test_" "temp_" "tmp_test_")

# Track findings
ARTIFACTS_FOUND=0
ARTIFACT_DETAILS=""

echo -e "${YELLOW}🔍 Verifying test cleanup...${NC}"

# Check for test services
echo "  Checking services directory..."
if [ -d "$PROJECT_ROOT/services" ]; then
    for prefix in "${TEST_PREFIXES[@]}"; do
        while IFS= read -r -d '' service_dir; do
            if [ -n "$service_dir" ]; then
                echo -e "    ${RED}✗${NC} Found test service: $(basename "$service_dir")"
                ARTIFACTS_FOUND=$((ARTIFACTS_FOUND + 1))
                ARTIFACT_DETAILS="${ARTIFACT_DETAILS}\n  - Service: $(basename "$service_dir")"
            fi
        done < <(find "$PROJECT_ROOT/services" -type d -name "${prefix}*" -print0 2>/dev/null)
    done
fi

# Check for test Docker containers
echo "  Checking Docker containers..."
if command -v docker &> /dev/null; then
    for prefix in "${TEST_PREFIXES[@]}"; do
        containers=$(docker ps -a --filter "name=${prefix}" --format "{{.Names}}" 2>/dev/null || true)
        if [ -n "$containers" ]; then
            while IFS= read -r container; do
                if [ -n "$container" ]; then
                    echo -e "    ${RED}✗${NC} Found test container: $container"
                    ARTIFACTS_FOUND=$((ARTIFACTS_FOUND + 1))
                    ARTIFACT_DETAILS="${ARTIFACT_DETAILS}\n  - Container: $container"
                fi
            done <<< "$containers"
        fi
    done
else
    echo -e "    ${YELLOW}⚠${NC} Docker not available, skipping container check"
fi

# Check for test Pulumi stacks
echo "  Checking Pulumi stacks..."
if command -v pulumi &> /dev/null; then
    stacks=$(pulumi stack ls --json 2>/dev/null || echo "[]")
    for prefix in "${TEST_PREFIXES[@]}"; do
        test_stacks=$(echo "$stacks" | jq -r --arg prefix "$prefix" '.[] | select(.name | contains($prefix)) | .name' 2>/dev/null || true)
        if [ -n "$test_stacks" ]; then
            while IFS= read -r stack; do
                if [ -n "$stack" ]; then
                    echo -e "    ${RED}✗${NC} Found test stack: $stack"
                    ARTIFACTS_FOUND=$((ARTIFACTS_FOUND + 1))
                    ARTIFACT_DETAILS="${ARTIFACT_DETAILS}\n  - Stack: $stack"
                fi
            done <<< "$test_stacks"
        fi
    done
else
    echo -e "    ${YELLOW}⚠${NC} Pulumi not available, skipping stack check"
fi

# Check for test processes
echo "  Checking for test processes..."
for prefix in "${TEST_PREFIXES[@]}"; do
    processes=$(ps aux | grep -E "${prefix}" | grep -v grep | grep -v "$0" || true)
    if [ -n "$processes" ]; then
        while IFS= read -r process_line; do
            if [ -n "$process_line" ]; then
                pid=$(echo "$process_line" | awk '{print $2}')
                cmd=$(echo "$process_line" | awk '{for(i=11;i<=NF;i++) printf "%s ", $i; print ""}')
                echo -e "    ${RED}✗${NC} Found test process: PID $pid - ${cmd:0:50}..."
                ARTIFACTS_FOUND=$((ARTIFACTS_FOUND + 1))
                ARTIFACT_DETAILS="${ARTIFACT_DETAILS}\n  - Process: PID $pid"
            fi
        done <<< "$processes"
    fi
done

# Check for temporary files in common locations
echo "  Checking for temporary files..."
TEMP_DIRS=("/tmp" "/var/tmp" "$HOME/.cache")
for temp_dir in "${TEMP_DIRS[@]}"; do
    if [ -d "$temp_dir" ]; then
        for prefix in "${TEST_PREFIXES[@]}"; do
            temp_files=$(find "$temp_dir" -maxdepth 2 -name "${prefix}*" 2>/dev/null || true)
            if [ -n "$temp_files" ]; then
                while IFS= read -r temp_file; do
                    if [ -n "$temp_file" ]; then
                        echo -e "    ${RED}✗${NC} Found temp file: $temp_file"
                        ARTIFACTS_FOUND=$((ARTIFACTS_FOUND + 1))
                        ARTIFACT_DETAILS="${ARTIFACT_DETAILS}\n  - Temp: $temp_file"
                    fi
                done <<< "$temp_files"
            fi
        done
    fi
done

# Summary
echo ""
if [ $ARTIFACTS_FOUND -eq 0 ]; then
    echo -e "${GREEN}✅ Verification complete - no test artifacts found!${NC}"
    exit 0
else
    echo -e "${RED}⚠️  Found $ARTIFACTS_FOUND test artifacts:${NC}"
    echo -e "$ARTIFACT_DETAILS"
    echo ""
    echo -e "${YELLOW}To clean up, run:${NC}"
    echo "  make clean-test-artifacts"
    echo ""
    echo -e "${YELLOW}For emergency cleanup, run:${NC}"
    echo "  make clean-all-test-artifacts"
    exit 1
fi
