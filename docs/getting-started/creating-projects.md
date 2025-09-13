# Creating Projects from Template

This guide explains how to create new projects from the Pantstack template.

## Methods Overview

There are three ways to create a project from this template:

1. **Cruft (Recommended)** - Interactive prompts with variable substitution
2. **GitHub UI** - Simple copy via "Use this template" button
3. **Local Template** - Using local copy of the template

## Method 1: Using Cruft (Recommended)

Cruft provides the best experience with automatic variable substitution and template updates.

### Install Cruft

```bash
# Using pipx (recommended)
pipx install cruft

# Or using pip
pip install --user cruft
```

### Create Your Project

```bash
# Create from the template
cruft create gh:MehdiZare/pantstack

# You'll be prompted for:
# - project_slug: Your project name
# - github_owner: Your GitHub username/org
# - github_repo: Repository name
# - aws_account_id: AWS account ID
# - aws_region: AWS region
# - pulumi_org: Pulumi organization
```

### Benefits of Cruft

- Automatic variable substitution
- Track template version
- Update from template later: `cruft update`
- Check for updates: `cruft check`

## Method 2: GitHub Template UI

Simple but requires manual configuration.

### Steps

1. Visit https://github.com/MehdiZare/pantstack
2. Click "Use this template" button
3. Choose "Create a new repository"
4. Fill in repository details
5. Clone your new repository

### Post-Creation Setup

```bash
# Clone your new repo
git clone https://github.com/YOUR_USERNAME/YOUR_REPO
cd YOUR_REPO

# Update .env file
cp .env.example .env
# Edit .env - replace any {{ cookiecutter.* }} placeholders
```

## Method 3: Local Template

If you have the template cloned locally:

```bash
# From the template directory
make new-project

# Follow the interactive prompts
```

## Post-Creation Setup

Regardless of the method used, complete these setup steps:

### 1. Configure Environment

```bash
cd your-project-name
cp .env.example .env
```

Edit `.env` with your actual values:
- AWS credentials
- Pulumi access token
- Project configuration

### 2. Bootstrap Infrastructure

```bash
# Creates GitHub repo, ECR, CI/CD setup
make bootstrap
```

### 3. Initialize Stacks

```bash
# Initialize Pulumi stacks for all environments
make seed-stacks
```

### 4. Push to GitHub

```bash
git add .
git commit -m "Initial project setup"
git push -u origin dev
```

## Project Structure

Your new project will have:

```
your-project/
├── modules/           # Service modules
│   └── api/          # Example API module
├── platform/         # Shared platform code
├── .github/          # GitHub Actions workflows
├── pants.toml        # Pants build configuration
├── docker-compose.yml # Local development
└── Makefile          # Common commands
```

## Verification

After setup, verify your project:

```bash
# Run tests
make test

# Start local development
make up

# Check CI/CD
git push origin dev  # Should trigger CI
```

## Customization

Common first customizations:

1. **Remove example module**: Delete `modules/api` if not needed
2. **Add your modules**: `make new-module M=your-service`
3. **Update README**: Customize for your project
4. **Configure domains**: Update infrastructure configs

## Troubleshooting

### Missing Dependencies

```bash
# Install Pants
make boot

# Install pre-commit hooks
make pre-commit-install
```

### AWS/Pulumi Issues

- Ensure AWS credentials are configured
- Verify Pulumi token is valid
- Check AWS region settings

## Next Steps

- [Module Development](../development/module-development.md)
- [Infrastructure Setup](../architecture/infrastructure.md)
- [CI/CD Configuration](../architecture/cicd.md)
