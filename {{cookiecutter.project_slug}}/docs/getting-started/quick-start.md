# Quick Start Guide

This guide will help you get started with the Pantstack template quickly.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Git**: Version control system
- **GitHub CLI** (`gh`): For GitHub operations
- **Python 3.12**: Required for Pants and services (repo pins 3.12.*)
- **Docker**: For local development and packaging
- **AWS CLI**: For AWS deployments (optional for template)
- **Pulumi CLI**: For infrastructure management (optional for template)

## Choose Your Path

### 🎯 I want to publish this as a template

If you're setting up this repository as a reusable template for others:

1. **Authenticate with GitHub**:
   ```bash
   gh auth login
   gh auth refresh -s workflow  # Required for workflows
   ```

2. **Configure and publish**:
   ```bash
   make template-setup  # Complete template setup
   ```

This will:
- Create release labels
- Publish to GitHub as a template
- Set up versioning system

### 📦 I want to create a new project

If you want to create a new project from this template:

1. **Install Cruft** (for template updates):
   ```bash
   pipx install cruft
   ```

2. **Create your project**:
   ```bash
   cruft create gh:MehdiZare/pantstack
   ```

3. **Set up your project**:
   ```bash
   cd your-project-name
   cp .env.example .env  # Edit with your values
   make bootstrap        # Set up GitHub, ECR, CI/CD
   make seed-stacks      # Initialize Pulumi stacks
   ```

## Next Steps

- [Template Setup](template-setup.md) - Detailed template configuration
- [Creating Projects](creating-projects.md) - Project creation guide
- [Commands Reference](../development/commands.md) - Available make commands
- [Architecture Overview](../architecture/overview.md) - System design
