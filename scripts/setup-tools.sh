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
echo -e "${CYAN}       Pantstack Development Environment Setup${RESET}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""

# Detect OS
OS_TYPE="unknown"
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS_TYPE="macos"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS_TYPE="linux"
else
    echo -e "${RED}❌ Unsupported OS: $OSTYPE${RESET}"
    exit 1
fi

echo -e "${BLUE}📍 Detected OS: ${OS_TYPE}${RESET}"
echo ""

# Required tools with versions
declare -A TOOLS=(
    ["python3"]="3.11+"
    ["uv"]="0.4+"
    ["docker"]="20.10+"
    ["aws"]="2.0+"
    ["pulumi"]="3.0+"
    ["gh"]="2.0+"
    ["supabase"]="1.0+"
    ["pants"]="2.28+"
    ["jq"]="1.6+"
    ["cruft"]="2.0+"
)

# Check function
check_tool() {
    local tool=$1
    local required_version=$2

    if command -v "$tool" &> /dev/null; then
        echo -e "${GREEN}✓${RESET} $tool is installed"
        return 0
    else
        echo -e "${YELLOW}⚠${RESET}  $tool is not installed (required: $required_version)"
        return 1
    fi
}

# Installation functions
install_homebrew() {
    if ! command -v brew &> /dev/null; then
        echo -e "${YELLOW}Installing Homebrew...${RESET}"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

        # Add Homebrew to PATH
        if [[ -d "/opt/homebrew" ]]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        else
            eval "$(/usr/local/bin/brew shellenv)"
        fi
    fi
}

install_tool_macos() {
    local tool=$1

    case $tool in
        python3)
            brew install python@3.11
            ;;
        uv)
            brew install uv
            ;;
        docker)
            echo -e "${YELLOW}Please install Docker Desktop from: https://www.docker.com/products/docker-desktop${RESET}"
            echo "Press Enter after installation..."
            read
            ;;
        aws)
            brew install awscli
            ;;
        pulumi)
            brew install pulumi
            ;;
        gh)
            brew install gh
            ;;
        supabase)
            brew install supabase/tap/supabase
            ;;
        pants)
            curl --proto '=https' --tlsv1.2 -fsSL https://static.pantsbuild.org/setup/get-pants.sh | bash
            echo -e "${YELLOW}Note: Add \$HOME/.local/bin to your PATH${RESET}"
            ;;
        jq)
            brew install jq
            ;;
        cruft)
            if command -v uv &> /dev/null; then
                uv tool install cruft
            elif command -v pipx &> /dev/null; then
                pipx install cruft
            else
                pip3 install --user cruft
            fi
            ;;
    esac
}

install_tool_linux() {
    local tool=$1

    case $tool in
        python3)
            sudo apt update && sudo apt install -y python3.11 python3.11-venv python3-pip
            ;;
        uv)
            curl -LsSf https://astral.sh/uv/install.sh | sh
            ;;
        docker)
            curl -fsSL https://get.docker.com | sh
            sudo usermod -aG docker $USER
            echo -e "${YELLOW}Note: You need to log out and back in for docker group changes${RESET}"
            ;;
        aws)
            curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
            unzip awscliv2.zip
            sudo ./aws/install
            rm -rf awscliv2.zip aws/
            ;;
        pulumi)
            curl -fsSL https://get.pulumi.com | sh
            echo -e "${YELLOW}Note: Add \$HOME/.pulumi/bin to your PATH${RESET}"
            ;;
        gh)
            type -p curl >/dev/null || sudo apt install curl -y
            curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
            sudo apt update && sudo apt install gh -y
            ;;
        supabase)
            if command -v brew &> /dev/null; then
                brew install supabase/tap/supabase
            else
                wget -qO- https://github.com/supabase/cli/releases/latest/download/supabase_linux_amd64.deb -O /tmp/supabase.deb
                sudo dpkg -i /tmp/supabase.deb
                rm /tmp/supabase.deb
            fi
            ;;
        pants)
            curl --proto '=https' --tlsv1.2 -fsSL https://static.pantsbuild.org/setup/get-pants.sh | bash
            echo -e "${YELLOW}Note: Add \$HOME/.local/bin to your PATH${RESET}"
            ;;
        jq)
            sudo apt install -y jq
            ;;
        cruft)
            if command -v uv &> /dev/null; then
                uv tool install cruft
            elif command -v pipx &> /dev/null; then
                pipx install cruft
            else
                pip3 install --user cruft
            fi
            ;;
    esac
}

# Check all tools
echo -e "${BLUE}🔍 Checking required tools...${RESET}"
echo ""

MISSING_TOOLS=()
for tool in "${!TOOLS[@]}"; do
    if ! check_tool "$tool" "${TOOLS[$tool]}"; then
        MISSING_TOOLS+=("$tool")
    fi
done

# Install missing tools
if [ ${#MISSING_TOOLS[@]} -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}📦 Missing tools: ${MISSING_TOOLS[*]}${RESET}"
    echo ""
    read -p "Would you like to install missing tools? (y/N): " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [[ "$OS_TYPE" == "macos" ]]; then
            install_homebrew
        fi

        for tool in "${MISSING_TOOLS[@]}"; do
            echo ""
            echo -e "${BLUE}Installing $tool...${RESET}"
            if [[ "$OS_TYPE" == "macos" ]]; then
                install_tool_macos "$tool"
            else
                install_tool_linux "$tool"
            fi
        done
    fi
else
    echo ""
    echo -e "${GREEN}✅ All required tools are installed!${RESET}"
fi

# Additional setup steps
echo ""
echo -e "${BLUE}🔧 Additional Setup Steps${RESET}"
echo ""

# Python virtual environment
if ! [ -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    if command -v uv &> /dev/null; then
        uv venv .venv
    else
        python3 -m venv .venv
    fi
    echo -e "${GREEN}✓ Virtual environment created${RESET}"
else
    echo -e "${GREEN}✓ Virtual environment exists${RESET}"
fi

# GitHub CLI authentication
if ! gh auth status &> /dev/null 2>&1; then
    echo -e "${YELLOW}⚠ GitHub CLI is not authenticated${RESET}"
    echo "  Run: gh auth login"
    echo "  Then: gh auth refresh -s workflow"
else
    echo -e "${GREEN}✓ GitHub CLI is authenticated${RESET}"
fi

# AWS CLI configuration
if ! aws sts get-caller-identity &> /dev/null 2>&1; then
    echo -e "${YELLOW}⚠ AWS CLI is not configured${RESET}"
    echo "  Run: aws configure"
else
    echo -e "${GREEN}✓ AWS CLI is configured${RESET}"
fi

# Pulumi login
if ! pulumi whoami &> /dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Pulumi is not logged in${RESET}"
    echo "  Run: pulumi login"
else
    echo -e "${GREEN}✓ Pulumi is logged in${RESET}"
fi

# Docker daemon check
if ! docker info &> /dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Docker daemon is not running${RESET}"
    echo "  Please start Docker Desktop or Docker service"
else
    echo -e "${GREEN}✓ Docker is running${RESET}"
fi

# PATH setup
echo ""
echo -e "${BLUE}📝 Environment Setup${RESET}"
echo ""
echo "Add these to your shell profile (~/.bashrc, ~/.zshrc, etc.):"
echo ""
echo -e "${CYAN}# Pantstack paths${RESET}"
echo 'export PATH="$HOME/.local/bin:$PATH"'
echo 'export PATH="$HOME/.pulumi/bin:$PATH"'
echo ''
echo -e "${CYAN}# Activate virtual environment (optional)${RESET}"
echo 'source .venv/bin/activate'

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "${GREEN}              Setup Complete! Next Steps:${RESET}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""
echo "1. Source your shell profile or restart terminal"
echo "2. Authenticate tools if needed:"
echo "   - gh auth login && gh auth refresh -s workflow"
echo "   - aws configure"
echo "   - pulumi login"
echo "3. Initialize the project:"
echo "   - cp .env.local .env"
echo "   - supabase init && supabase start"
echo "   - make up"
echo ""