# Template Setup Guide

This guide walks you through setting up the Pantstack template repository.

## Prerequisites

- GitHub account
- GitHub CLI installed and authenticated
- Git configured locally

## Initial Setup

### 1. Fork or Clone the Template

```bash
git clone https://github.com/MehdiZare/pantstack.git
cd pantstack
```

### 2. Configure GitHub Authentication

```bash
# Login to GitHub CLI
gh auth login

# Add workflow scope (required for GitHub Actions)
gh auth refresh -s workflow
```

### 3. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your values:
# - GITHUB_OWNER: Your GitHub username
# - GITHUB_REPO: Your desired repository name
# - Leave GITHUB_TOKEN empty (uses gh CLI)
```

## Complete Template Setup

Run the all-in-one setup command:

```bash
make template-setup
```

This command will:
1. Publish the repository to GitHub
2. Mark it as a template
3. Create release labels
4. Configure repository settings

## Manual Setup Steps

If you prefer to run steps individually:

```bash
# 1. Initialize and publish template
make init-template

# 2. Create release labels
make seed-labels

# 3. Build and serve docs locally
make docs-serve
```

## Verify Setup

After setup, verify everything is working:

1. **Check GitHub Repository**:
   - Visit `https://github.com/YOUR_USERNAME/YOUR_REPO`
   - Confirm "Use this template" button appears
   - Check Settings → verify it's marked as a template

2. **Check Release Labels**:
   - Go to Issues → Labels
   - Verify release labels exist:
     - release:major (red)
     - release:minor (green)
     - release:patch (blue)
     - release:skip (light purple)

3. **Check Workflows**:
   - Go to Actions tab
   - Workflows should be visible but skipped

## Next Steps

- [Creating Projects](creating-projects.md) - How to use your template
- [Versioning](../development/versioning.md) - Managing template versions
- [Contributing](../template/contributing.md) - Contributing guidelines