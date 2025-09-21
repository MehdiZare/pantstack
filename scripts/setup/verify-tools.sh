#!/usr/bin/env bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
RESET='\033[0m'

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "${CYAN}          Verifying Development Tools${RESET}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""

# Track status
ALL_GOOD=true
MISSING_TOOLS=()

# Check function with version extraction
check_tool_version() {
    local tool=$1
    local min_version=$2
    local version_cmd=$3

    if command -v "$tool" &> /dev/null; then
        if [ -n "$version_cmd" ]; then
            version=$(eval "$version_cmd" 2>/dev/null || echo "unknown")
            echo -e "${GREEN}✓${RESET} $tool: $version"
        else
            echo -e "${GREEN}✓${RESET} $tool: installed"
        fi
        return 0
    else
        echo -e "${RED}✗${RESET} $tool: not found (need $min_version)"
        MISSING_TOOLS+=("$tool")
        ALL_GOOD=false
        return 1
    fi
}

# Core tools
echo -e "${BLUE}Core Tools:${RESET}"
check_tool_version "python3" "3.11+" "python3 --version | awk '{print \$2}'"
check_tool_version "uv" "0.4+" "uv --version | awk '{print \$2}'"
check_tool_version "docker" "20.10+" "docker --version | awk '{print \$3}' | sed 's/,//'"
check_tool_version "docker-compose" "2.0+" "docker compose version | awk '{print \$4}'"

echo ""
echo -e "${BLUE}Infrastructure Tools:${RESET}"
check_tool_version "aws" "2.0+" "aws --version | awk '{print \$1}' | cut -d'/' -f2"
check_tool_version "pulumi" "3.0+" "pulumi version | head -1"
check_tool_version "gh" "2.0+" "gh --version | head -1 | awk '{print \$3}'"

echo ""
echo -e "${BLUE}Development Tools:${RESET}"
check_tool_version "supabase" "1.0+" "supabase --version | awk '{print \$3}'"
check_tool_version "pants" "2.28+" "./pants --version 2>/dev/null || echo 'not installed'"
check_tool_version "jq" "1.6+" "jq --version | sed 's/jq-//'"
check_tool_version "cruft" "2.0+" "cruft --version 2>/dev/null | awk '{print \$3}' || echo 'not installed'"

echo ""
echo -e "${BLUE}Service Status:${RESET}"

# Check Docker daemon
if docker info &> /dev/null; then
    echo -e "${GREEN}✓${RESET} Docker daemon: running"
else
    echo -e "${YELLOW}⚠${RESET}  Docker daemon: not running"
fi

# Check Supabase status
if supabase status &> /dev/null 2>&1; then
    echo -e "${GREEN}✓${RESET} Supabase: running"
else
    echo -e "${YELLOW}⚠${RESET}  Supabase: not running (run 'supabase start')"
fi

# Check LocalStack
if docker ps --format "table {{.Names}}" | grep -q localstack; then
    echo -e "${GREEN}✓${RESET} LocalStack: running"
else
    echo -e "${YELLOW}⚠${RESET}  LocalStack: not running (run 'make localstack-up')"
fi

echo ""
echo -e "${BLUE}Authentication Status:${RESET}"

# GitHub CLI
if gh auth status &> /dev/null 2>&1; then
    user=$(gh api user --jq .login 2>/dev/null || echo "unknown")
    echo -e "${GREEN}✓${RESET} GitHub CLI: authenticated as $user"
else
    echo -e "${YELLOW}⚠${RESET}  GitHub CLI: not authenticated"
fi

# AWS CLI
if aws sts get-caller-identity &> /dev/null 2>&1; then
    account=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)
    echo -e "${GREEN}✓${RESET} AWS CLI: configured (account: $account)"
else
    echo -e "${YELLOW}⚠${RESET}  AWS CLI: not configured"
fi

# Pulumi
if pulumi whoami &> /dev/null 2>&1; then
    user=$(pulumi whoami 2>/dev/null)
    echo -e "${GREEN}✓${RESET} Pulumi: logged in as $user"
else
    echo -e "${YELLOW}⚠${RESET}  Pulumi: not logged in"
fi

# Python environment
echo ""
echo -e "${BLUE}Python Environment:${RESET}"

if [ -d ".venv" ]; then
    echo -e "${GREEN}✓${RESET} Virtual environment: exists"
    if [ -n "${VIRTUAL_ENV:-}" ]; then
        echo -e "${GREEN}✓${RESET} Virtual environment: activated"
    else
        echo -e "${YELLOW}⚠${RESET}  Virtual environment: not activated (run 'source .venv/bin/activate')"
    fi
else
    echo -e "${YELLOW}⚠${RESET}  Virtual environment: not found (run 'uv venv .venv')"
fi

# Summary
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"

if [ "$ALL_GOOD" = true ] && [ ${#MISSING_TOOLS[@]} -eq 0 ]; then
    echo -e "${GREEN}✅ All required tools are installed!${RESET}"
else
    echo -e "${RED}❌ Missing tools detected!${RESET}"
    echo ""
    echo "Missing: ${MISSING_TOOLS[*]}"
    echo ""
    echo "Run 'make setup' to install missing tools"
fi

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"

# Exit with error if tools are missing
if [ "$ALL_GOOD" = false ]; then
    exit 1
fi