# Required Development Tools

This document lists all tools required for developing with Pantstack and provides installation instructions for different operating systems.

## Quick Setup

The easiest way to install all required tools:

```bash
# Interactive setup with prompts
make setup

# Quick setup without prompts
make setup-quick

# Verify installations
make check-tools
```

## Core Requirements

### Python 3.11+
The primary programming language for all services.

**macOS:**
```bash
brew install python@3.11
```

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install -y python3.11 python3.11-venv python3-pip
```

### uv (0.4+)
Fast Python package installer and virtual environment manager.

**All platforms:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**macOS with Homebrew:**
```bash
brew install uv
```

### Docker (20.10+) & Docker Compose
Container runtime for local development and deployment.

**macOS:**
- Download and install [Docker Desktop](https://www.docker.com/products/docker-desktop/)

**Linux:**
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Log out and back in for group changes
```

## Infrastructure Tools

### AWS CLI (2.0+)
For managing AWS resources and LocalStack.

**macOS:**
```bash
brew install awscli
```

**Linux:**
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
rm -rf awscliv2.zip aws/
```

### Pulumi (3.0+)
Infrastructure as Code for deploying to AWS.

**macOS:**
```bash
brew install pulumi
```

**Linux:**
```bash
curl -fsSL https://get.pulumi.com | sh
# Add $HOME/.pulumi/bin to PATH
```

### LocalStack
Local AWS cloud emulation (runs via Docker).

LocalStack is included in the docker-compose.yml file and doesn't require separate installation.

## Development Tools

### Pants (2.28+)
Build system for monorepo management.

**All platforms:**
```bash
curl --proto '=https' --tlsv1.2 -fsSL https://static.pantsbuild.org/setup/get-pants.sh | bash
# Add $HOME/.local/bin to PATH
```

### Supabase CLI (1.0+)
Database, authentication, and storage management.

**macOS:**
```bash
brew install supabase/tap/supabase
```

**Linux:**
```bash
# Option 1: Via .deb package
wget -qO- https://github.com/supabase/cli/releases/latest/download/supabase_linux_amd64.deb -O /tmp/supabase.deb
sudo dpkg -i /tmp/supabase.deb

# Option 2: Via Homebrew on Linux
brew install supabase/tap/supabase
```

### GitHub CLI (2.0+)
Repository and workflow management.

**macOS:**
```bash
brew install gh
```

**Linux:**
```bash
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update && sudo apt install gh -y
```

### jq (1.6+)
JSON processing utility.

**macOS:**
```bash
brew install jq
```

**Linux:**
```bash
sudo apt install -y jq
```

### cruft (2.0+)
Template management for creating projects from Cookiecutter templates.

**With uv (recommended):**
```bash
uv tool install cruft
```

**With pipx:**
```bash
pipx install cruft
```

**With pip:**
```bash
pip install --user cruft
```

## Optional Tools

### pipx
Python application installer (alternative to pip for CLI tools).

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

### direnv
Automatic environment variable management.

**macOS:**
```bash
brew install direnv
```

**Linux:**
```bash
sudo apt install direnv
```

### pre-commit
Git hooks for code quality.

```bash
pip install --user pre-commit
# Or with uv
uv tool install pre-commit
```

## Authentication Setup

After installing the tools, you need to authenticate:

### GitHub CLI
```bash
gh auth login
gh auth refresh -s workflow  # Add workflow scope for CI/CD
```

### AWS CLI
```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and preferred region
```

### Pulumi
```bash
pulumi login
# Follow prompts to login to Pulumi Cloud (free tier available)
```

## Environment Setup

### PATH Configuration

Add these lines to your shell profile (`~/.bashrc`, `~/.zshrc`, or `~/.bash_profile`):

```bash
# Pants build system
export PATH="$HOME/.local/bin:$PATH"

# Pulumi
export PATH="$HOME/.pulumi/bin:$PATH"

# Python user packages (if using pip install --user)
export PATH="$HOME/.local/bin:$PATH"

# Homebrew (macOS with Apple Silicon)
eval "$(/opt/homebrew/bin/brew shellenv)"

# Homebrew (macOS with Intel)
eval "$(/usr/local/bin/brew shellenv)"
```

### Python Virtual Environment

Create and activate a virtual environment:

```bash
# Create virtual environment
uv venv .venv

# Activate (bash/zsh)
source .venv/bin/activate

# Activate (fish)
source .venv/bin/activate.fish

# Activate (Windows)
.venv\Scripts\activate
```

## Verification

Run the verification script to ensure all tools are properly installed:

```bash
make check-tools
```

This will check:
- Tool installations and versions
- Service status (Docker, Supabase, LocalStack)
- Authentication status (GitHub, AWS, Pulumi)
- Python environment setup

## Troubleshooting

### Docker permission denied (Linux)

If you get permission errors with Docker:
```bash
sudo usermod -aG docker $USER
# Log out and log back in
```

### Command not found after installation

Make sure the installation directory is in your PATH:
```bash
echo $PATH
# Should include $HOME/.local/bin and other tool paths
```

### LocalStack init scripts permission denied

Make scripts executable:
```bash
chmod +x .localstack/init/ready.d/*.sh
```

### Supabase port conflicts

If ports are already in use, stop conflicting services or modify Supabase config:
```bash
supabase stop
# Check what's using the ports
lsof -i :54321
lsof -i :54322
```

## Platform-Specific Notes

### macOS
- Homebrew is the recommended package manager
- Docker Desktop includes Docker Compose
- Some tools may require Xcode Command Line Tools: `xcode-select --install`

### Linux
- Use system package manager (apt, yum, etc.) when possible
- Docker requires logout/login after adding user to docker group
- Some tools may require build essentials: `sudo apt install build-essential`

### Windows (WSL2)
- Install tools inside WSL2, not Windows
- Use Ubuntu or Debian distribution
- Docker Desktop with WSL2 backend recommended