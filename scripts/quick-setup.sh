#!/usr/bin/env bash
set -euo pipefail

# Quick setup script for experienced users
# Installs all tools without prompts

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
RESET='\033[0m'

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "${CYAN}           Pantstack Quick Setup${RESET}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "${BLUE}📍 macOS detected - using Homebrew${RESET}"

    # Install Homebrew if needed
    if ! command -v brew &> /dev/null; then
        echo "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

        if [[ -d "/opt/homebrew" ]]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        else
            eval "$(/usr/local/bin/brew shellenv)"
        fi
    fi

    echo ""
    echo -e "${BLUE}Installing tools via Homebrew...${RESET}"

    # Install all tools at once
    brew install python@3.11 uv awscli pulumi gh jq
    brew install supabase/tap/supabase

    echo ""
    echo -e "${BLUE}Installing Pants build system...${RESET}"
    curl --proto '=https' --tlsv1.2 -fsSL https://static.pantsbuild.org/setup/get-pants.sh | bash

    echo ""
    echo -e "${BLUE}Installing Python tools...${RESET}"

    # Install cruft
    if command -v uv &> /dev/null; then
        uv tool install cruft
    elif command -v pipx &> /dev/null; then
        pipx install cruft
    else
        pip3 install --user cruft
    fi

    echo ""
    echo -e "${BLUE}Creating Python virtual environment...${RESET}"
    uv venv .venv

elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo -e "${BLUE}📍 Linux detected - using apt/curl${RESET}"

    # Update package manager
    sudo apt update

    echo ""
    echo -e "${BLUE}Installing system packages...${RESET}"
    sudo apt install -y python3.11 python3.11-venv python3-pip curl wget unzip jq

    echo ""
    echo -e "${BLUE}Installing uv...${RESET}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.local/bin/env

    echo ""
    echo -e "${BLUE}Installing AWS CLI...${RESET}"
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip -q awscliv2.zip
    sudo ./aws/install
    rm -rf awscliv2.zip aws/

    echo ""
    echo -e "${BLUE}Installing Pulumi...${RESET}"
    curl -fsSL https://get.pulumi.com | sh

    echo ""
    echo -e "${BLUE}Installing GitHub CLI...${RESET}"
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
    sudo apt update && sudo apt install gh -y

    echo ""
    echo -e "${BLUE}Installing Supabase CLI...${RESET}"
    wget -qO- https://github.com/supabase/cli/releases/latest/download/supabase_linux_amd64.deb -O /tmp/supabase.deb
    sudo dpkg -i /tmp/supabase.deb
    rm /tmp/supabase.deb

    echo ""
    echo -e "${BLUE}Installing Docker...${RESET}"
    if ! command -v docker &> /dev/null; then
        curl -fsSL https://get.docker.com | sh
        sudo usermod -aG docker $USER
        echo -e "${YELLOW}⚠ You need to log out and back in for docker group changes${RESET}"
    fi

    echo ""
    echo -e "${BLUE}Installing Pants build system...${RESET}"
    curl --proto '=https' --tlsv1.2 -fsSL https://static.pantsbuild.org/setup/get-pants.sh | bash

    echo ""
    echo -e "${BLUE}Installing Python tools...${RESET}"
    uv tool install cruft

    echo ""
    echo -e "${BLUE}Creating Python virtual environment...${RESET}"
    uv venv .venv

else
    echo -e "${YELLOW}⚠ Unsupported OS: $OSTYPE${RESET}"
    echo "Please use the manual setup instructions"
    exit 1
fi

# Create .env file if needed
if [ ! -f .env ]; then
    if [ -f .env.local ]; then
        echo ""
        echo -e "${BLUE}Creating .env from .env.local...${RESET}"
        cp .env.local .env
    elif [ -f .env.example ]; then
        echo ""
        echo -e "${BLUE}Creating .env from .env.example...${RESET}"
        cp .env.example .env
        echo -e "${YELLOW}⚠ Please edit .env with your actual values${RESET}"
    fi
fi

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "${GREEN}        ✅ Quick Setup Complete!${RESET}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""
echo "Next steps:"
echo ""
echo "1. Add to your shell profile (~/.bashrc or ~/.zshrc):"
echo '   export PATH="$HOME/.local/bin:$PATH"'
echo '   export PATH="$HOME/.pulumi/bin:$PATH"'
echo ""
echo "2. Authenticate tools:"
echo "   gh auth login && gh auth refresh -s workflow"
echo "   aws configure"
echo "   pulumi login"
echo ""
echo "3. Install Docker Desktop (if not installed):"
echo "   https://www.docker.com/products/docker-desktop"
echo ""
echo "4. Start development:"
echo "   source .venv/bin/activate"
echo "   supabase init && supabase start"
echo "   make up"
echo ""
echo "Run 'make check-tools' to verify everything is installed correctly"