#!/usr/bin/env bash
set -euo pipefail

# Creates GitHub release labels for semantic versioning
# Uses gh CLI for authentication

COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_RED='\033[0;31m'
COLOR_RESET='\033[0m'

# Check for gh CLI
if ! command -v gh >/dev/null 2>&1; then
  echo -e "${COLOR_RED}Error: GitHub CLI (gh) is not installed${COLOR_RESET}"
  echo "Install with: brew install gh (macOS) or see https://cli.github.com"
  exit 1
fi

# Check authentication
if ! gh auth status >/dev/null 2>&1; then
  echo -e "${COLOR_RED}Error: Not authenticated with GitHub${COLOR_RESET}"
  echo "Run: gh auth login"
  exit 1
fi

# Get repository info
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || true)
if [ -z "$REPO" ]; then
  # Try to get from git remote
  REPO=$(git remote get-url origin | sed 's/.*github.com[:/]\(.*\)\.git/\1/' 2>/dev/null || true)
fi

if [ -z "$REPO" ]; then
  echo -e "${COLOR_RED}Error: Could not determine repository${COLOR_RESET}"
  echo "Make sure you're in a git repository with a GitHub remote"
  exit 1
fi

echo -e "${COLOR_GREEN}Creating release labels for: $REPO${COLOR_RESET}"
echo ""

# Define labels
declare -a LABELS=(
  "release:major|b60205|Breaking changes - triggers major version bump"
  "release:minor|0e8a16|New features - triggers minor version bump"
  "release:patch|1d76db|Bug fixes - triggers patch version bump"
  "release:skip|c5def5|Skip version bump (docs, CI, etc.)"
)

# Create or update each label
for label_def in "${LABELS[@]}"; do
  IFS='|' read -r name color description <<< "$label_def"

  # Check if label exists
  if gh label list --repo "$REPO" | grep -q "^$name"; then
    echo -e "${COLOR_YELLOW}✓${COLOR_RESET} Label '$name' already exists"
    # Update the label to ensure correct color and description
    gh label edit "$name" --repo "$REPO" --color "$color" --description "$description" 2>/dev/null || true
  else
    echo -e "${COLOR_GREEN}+${COLOR_RESET} Creating label '$name'"
    gh label create "$name" --repo "$REPO" --color "$color" --description "$description"
  fi
done

echo ""
echo -e "${COLOR_GREEN}✅ Release labels created successfully!${COLOR_RESET}"
echo ""
echo "You can now use these labels on PRs from dev to main:"
echo "  • release:major - Breaking changes (1.0.0 → 2.0.0)"
echo "  • release:minor - New features (1.0.0 → 1.1.0)"
echo "  • release:patch - Bug fixes (1.0.0 → 1.0.1)"
echo "  • release:skip  - No version bump"
