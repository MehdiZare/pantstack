#!/usr/bin/env bash
set -euo pipefail

# Template cleanup script for end users
# Removes template-specific files and directories that users don't need
# This script is run after creating a new project from the template

COLOR_CYAN='\033[0;36m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_RED='\033[0;31m'
COLOR_RESET='\033[0m'

echo -e "${COLOR_CYAN}🧹 Cleaning up template-specific files...${COLOR_RESET}"
echo ""

# Track what we're removing
REMOVED_ITEMS=()

# Function to safely remove directory
remove_dir() {
    local dir=$1
    local desc=$2
    if [ -d "$dir" ]; then
        rm -rf "$dir"
        echo -e "${COLOR_GREEN}✓${COLOR_RESET} Removed $desc"
        REMOVED_ITEMS+=("$desc")
    fi
}

# Function to safely remove file
remove_file() {
    local file=$1
    local desc=$2
    if [ -f "$file" ]; then
        rm -f "$file"
        echo -e "${COLOR_GREEN}✓${COLOR_RESET} Removed $desc"
        REMOVED_ITEMS+=("$desc")
    fi
}

# Remove template-specific directories
echo "Removing template development directories..."
remove_dir "cli" "CLI tests directory (template testing)"
remove_dir "tests/template" "Template validation tests"
remove_dir "tests/scripts" "Script validation tests"
remove_dir "tests/cli" "CLI integration tests"

# Remove template-specific scripts
echo ""
echo "Removing template management scripts..."
remove_file "scripts/publish_template.sh" "Template publishing script"
remove_file "scripts/create_project_from_template.sh" "Template creation script"
remove_file "scripts/quickstart.sh" "Template quickstart wizard"

# Remove template-specific GitHub workflows
echo ""
echo "Removing template GitHub workflows..."
remove_file ".github/workflows/template-release.yml" "Template release workflow"
remove_file ".github/workflows/test-template.yml" "Template testing workflow"

# Remove template-specific documentation
echo ""
echo "Removing template documentation..."
remove_file "docs/TEMPLATE_USAGE.md" "Template usage guide"
remove_file "TEMPLATE_README.md" "Template README"

# Remove this cleanup script itself
echo ""
echo "Removing cleanup script..."
remove_file "scripts/cleanup_template.sh" "This cleanup script"

# Clean up cookiecutter files if they exist
echo ""
echo "Removing cookiecutter configuration..."
remove_file "cookiecutter.json" "Cookiecutter configuration"
remove_file ".cruft.json" "Cruft configuration"
remove_dir "hooks" "Cookiecutter hooks directory"

# Update pants.toml to remove test resolvers for removed directories
if [ -f "pants.toml" ]; then
    echo ""
    echo "Cleaning up pants.toml..."
    # Remove cli_test resolver if it exists
    sed -i.bak '/cli_test = "lockfiles\/cli_test.lock"/d' pants.toml && rm pants.toml.bak 2>/dev/null || true
    echo -e "${COLOR_GREEN}✓${COLOR_RESET} Cleaned up pants.toml"
fi

# Clean up any orphaned lockfiles
if [ -d "lockfiles" ]; then
    echo ""
    echo "Cleaning up orphaned lockfiles..."
    [ -f "lockfiles/cli_test.lock" ] && rm -f "lockfiles/cli_test.lock" && echo -e "${COLOR_GREEN}✓${COLOR_RESET} Removed cli_test.lock"
    [ -f "lockfiles/template_test.lock" ] && rm -f "lockfiles/template_test.lock" && echo -e "${COLOR_GREEN}✓${COLOR_RESET} Removed template_test.lock"
fi

# Clean up 3rdparty requirements for removed components
if [ -d "3rdparty/python" ]; then
    echo ""
    echo "Cleaning up template requirements..."
    remove_file "3rdparty/python/requirements-cli-test.txt" "CLI test requirements"
    remove_file "3rdparty/python/requirements-template-test.txt" "Template test requirements"
fi

# Summary
echo ""
echo -e "${COLOR_GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${COLOR_RESET}"
echo -e "${COLOR_GREEN}✅ Template cleanup complete!${COLOR_RESET}"
echo -e "${COLOR_GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${COLOR_RESET}"
echo ""

if [ ${#REMOVED_ITEMS[@]} -gt 0 ]; then
    echo "Removed ${#REMOVED_ITEMS[@]} template-specific items"
    echo ""
fi

echo "Your monorepo is now ready for production use!"
echo ""
echo "Next steps:"
echo "1. Run 'make setup' to install development tools"
echo "2. Configure your .env file with your AWS and GitHub credentials"
echo "3. Run 'make bootstrap' to set up foundation infrastructure"
echo "4. Start creating services with 'make new-service S=<service-name>'"
echo ""
echo "For more information, see:"
echo "  - README.md for project overview"
echo "  - docs/CLI_COMMANDS.md for available commands"
echo "  - CLAUDE.md for AI assistant guidance"
