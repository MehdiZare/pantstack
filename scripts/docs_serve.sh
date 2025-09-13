#!/usr/bin/env bash
set -euo pipefail

# Serves documentation locally for preview
# Installs MkDocs if needed

COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_CYAN='\033[0;36m'
COLOR_RESET='\033[0m'

echo -e "${COLOR_CYAN}📚 Starting documentation server...${COLOR_RESET}"
echo ""

# Check if MkDocs is installed
if ! command -v mkdocs >/dev/null 2>&1; then
  echo -e "${COLOR_YELLOW}MkDocs not found. Installing...${COLOR_RESET}"
  
  # Try to install with pip
  if command -v pip >/dev/null 2>&1; then
    pip install --user mkdocs mkdocs-material mkdocs-mermaid2-plugin pymdown-extensions
  elif command -v pip3 >/dev/null 2>&1; then
    pip3 install --user mkdocs mkdocs-material mkdocs-mermaid2-plugin pymdown-extensions
  else
    echo -e "${COLOR_RED}Error: pip not found. Please install Python and pip first.${COLOR_RESET}"
    exit 1
  fi
  
  echo -e "${COLOR_GREEN}✓ MkDocs installed${COLOR_RESET}"
else
  echo -e "${COLOR_GREEN}✓ MkDocs found${COLOR_RESET}"
  
  # Check for required plugins
  if ! pip show mkdocs-material >/dev/null 2>&1; then
    echo -e "${COLOR_YELLOW}Installing MkDocs Material theme...${COLOR_RESET}"
    pip install --user mkdocs-material mkdocs-mermaid2-plugin pymdown-extensions
  fi
fi

# Check if docs directory exists
if [ ! -d "docs" ]; then
  echo -e "${COLOR_YELLOW}Warning: docs/ directory not found${COLOR_RESET}"
  echo "Creating basic docs structure..."
  mkdir -p docs
  if [ -f "README.md" ]; then
    cp README.md docs/index.md
  else
    echo "# Documentation" > docs/index.md
  fi
fi

# Start the server
echo ""
echo -e "${COLOR_GREEN}Starting MkDocs server...${COLOR_RESET}"
echo -e "${COLOR_CYAN}Documentation will be available at: http://localhost:8000${COLOR_RESET}"
echo -e "${COLOR_YELLOW}Press Ctrl+C to stop the server${COLOR_RESET}"
echo ""

# Run MkDocs serve with live reload
mkdocs serve --dev-addr=localhost:8000 --livereload