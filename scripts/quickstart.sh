#!/usr/bin/env bash
set -euo pipefail

# Interactive quickstart for Pantstack template
# Supports both template authors (publishing) and users (creating projects)

COLOR_CYAN='\033[0;36m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_RED='\033[0;31m'
COLOR_RESET='\033[0m'

echo -e "${COLOR_CYAN}🚀 Pantstack Template Quickstart${COLOR_RESET}"
echo ""
echo "Are you:"
echo "1) Setting up this template for others to use (Template Author)"
echo "2) Creating a new project from a template (Template User)"
echo ""
read -p "Enter choice (1 or 2): " choice

case $choice in
  1)
    echo -e "\n${COLOR_GREEN}Template Author Setup${COLOR_RESET}"
    echo "This will help you publish this repository as a reusable template."
    echo ""
    
    # Check for .env file
    if [ ! -f .env ]; then
      if [ -f .env.example ]; then
        echo "Creating .env from .env.example..."
        cp .env.example .env
        echo -e "${COLOR_YELLOW}Please edit .env with your values:${COLOR_RESET}"
        echo "  - GITHUB_OWNER: Your GitHub username or org"
        echo "  - GITHUB_REPO: Name for your template repository"
        echo "  - GITHUB_TOKEN: Your GitHub Personal Access Token"
        echo ""
        read -p "Press Enter after editing .env..."
      fi
    fi
    
    # Source .env
    if [ -f .env ]; then
      export $(grep -v '^#' .env | xargs)
    fi
    
    # Check required vars
    if [ -z "${GITHUB_OWNER:-}" ]; then
      read -p "GitHub owner (username or org): " GITHUB_OWNER
      export GITHUB_OWNER
    fi
    
    if [ -z "${GITHUB_REPO:-}" ]; then
      read -p "Template repository name [pantstack]: " GITHUB_REPO
      GITHUB_REPO=${GITHUB_REPO:-pantstack}
      export GITHUB_REPO
    fi
    
    echo -e "\n${COLOR_GREEN}Publishing template to GitHub...${COLOR_RESET}"
    ./scripts/publish_template.sh
    
    echo -e "\n${COLOR_GREEN}✅ Template published successfully!${COLOR_RESET}"
    echo ""
    echo "Your template is now available at:"
    echo -e "${COLOR_CYAN}https://github.com/$GITHUB_OWNER/$GITHUB_REPO${COLOR_RESET}"
    echo ""
    echo "Others can now use it via:"
    echo "  - Cookiecutter: cruft create gh:$GITHUB_OWNER/$GITHUB_REPO"
    echo "  - GitHub: Click 'Use this template' button on GitHub"
    ;;
    
  2)
    echo -e "\n${COLOR_GREEN}Creating New Project from Template${COLOR_RESET}"
    echo ""
    
    # Check for cruft/cookiecutter
    if ! command -v cruft >/dev/null 2>&1 && ! command -v cookiecutter >/dev/null 2>&1; then
      echo -e "${COLOR_YELLOW}Installing cruft (recommended over cookiecutter)...${COLOR_RESET}"
      if command -v pipx >/dev/null 2>&1; then
        pipx install cruft
      else
        pip install --user cruft
      fi
    fi
    
    # Determine tool
    if command -v cruft >/dev/null 2>&1; then
      TOOL="cruft"
      echo "Using cruft (supports template updates)"
    else
      TOOL="cookiecutter"
      echo "Using cookiecutter"
    fi
    
    # Get template source
    echo ""
    echo "Template source options:"
    echo "1) GitHub repository (e.g., gh:owner/repo)"
    echo "2) Local directory (this repository)"
    echo ""
    read -p "Enter choice (1 or 2): " source_choice
    
    case $source_choice in
      1)
        read -p "GitHub template (e.g., pantstack/mono-template): " template_source
        if [[ ! "$template_source" =~ ^gh: ]]; then
          template_source="gh:$template_source"
        fi
        ;;
      2)
        template_source="."
        ;;
      *)
        echo -e "${COLOR_RED}Invalid choice${COLOR_RESET}"
        exit 1
        ;;
    esac
    
    echo -e "\n${COLOR_GREEN}Creating project from template...${COLOR_RESET}"
    $TOOL create "$template_source"
    
    # Find the created directory
    if [ "$source_choice" = "1" ]; then
      dir=$(ls -td */ | head -n1)
      dir=${dir%/}
      
      echo -e "\n${COLOR_GREEN}✅ Project created successfully!${COLOR_RESET}"
      echo ""
      echo "Next steps:"
      echo -e "${COLOR_CYAN}cd $dir${COLOR_RESET}"
      echo -e "${COLOR_CYAN}cp .env.example .env${COLOR_RESET}  # Edit with your values"
      echo -e "${COLOR_CYAN}make bootstrap${COLOR_RESET}       # Setup GitHub repo, ECR, CI/CD"
      echo -e "${COLOR_CYAN}make seed-stacks${COLOR_RESET}     # Initialize Pulumi stacks"
      echo ""
      echo "Then push to GitHub:"
      echo -e "${COLOR_CYAN}git push -u origin dev${COLOR_RESET}"
    fi
    ;;
    
  *)
    echo -e "${COLOR_RED}Invalid choice. Please run again and select 1 or 2.${COLOR_RESET}"
    exit 1
    ;;
esac