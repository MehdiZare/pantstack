# Pantstack (services-first)

Pantstack is a batteries-included monorepo template for layered services with Pants, FastAPI, Pulumi on AWS, and GitHub Actions.

- Service independence (per-service resolves, infra, packaging, and tests)
- Safe cross-service reuse via `public/` facades and shared `stack/*` libs
- Single ECR per project; image tags encode service + branch + version
- CI/CD for lint, typecheck, tests, package, deploy, and PR preview stacks
- Pulumi Cloud (Free) backend; optional ESC (Environments) integration

Prerequisites:
- Python 3.12 (repo is pinned to 3.12.* in `pants.toml`)

## Quick Start (Template Author)

Prerequisites:
- GitHub CLI (`gh`) installed and authenticated: `gh auth login`
- Add workflow scope to GitHub CLI: `gh auth refresh -s workflow`

Steps to publish this as a template:

1) Create `.env` file with your configuration:
   ```bash
   cp .env.example .env
   # Edit .env and replace the {{ cookiecutter.* }} placeholders with actual values:
   # GITHUB_OWNER=YourGitHubUsername
   # GITHUB_REPO=your-template-name
   # Leave GITHUB_TOKEN empty to use gh CLI authentication
   ```

2) Publish the template:
   ```bash
   make init-template
   ```
   This will:
   - Create/update the GitHub repository
   - Push code to `dev` (default) and `main` branches
   - Mark repository as a GitHub template
   - Configure repository metadata and topics

3) Your template is now ready at: `https://github.com/YourUsername/your-template-name`

**Note**: The template repository has workflows that are configured to skip execution to avoid failures. These workflows will automatically activate when users create their own projects from the template.

## Template Versioning

This template follows [Semantic Versioning](https://semver.org/). All changes from `dev` to `main` require a version label:

- **release:major** - Breaking changes (e.g., 1.0.0 → 2.0.0)
- **release:minor** - New features (e.g., 1.0.0 → 1.1.0)
- **release:patch** - Bug fixes (e.g., 1.0.0 → 1.0.1)
- **release:skip** - No version bump (docs, CI tweaks)

### For Template Maintainers
1. Make changes in feature branches, PR to `dev`
2. When ready to release, PR from `dev` to `main` with a version label
3. On merge, automatic GitHub release with changelog

### For Template Users
- Check releases: https://github.com/MehdiZare/pantstack/releases
- Use specific version: `cruft create gh:MehdiZare/pantstack --checkout v1.2.3`
- Update existing project: `cruft update` (if using cruft)

## Create a New Project from the Template

### Option A: Cookiecutter with Variable Substitution (Recommended)

This method prompts you for project-specific values and automatically replaces template variables.

1) Install Cruft (enhanced Cookiecutter):
   ```bash
   pipx install cruft  # or: pip install --user cruft
   ```

2) Create project from template:
   ```bash
   cruft create gh:MehdiZare/pantstack
   # You'll be prompted for:
   # - project_slug (your project name)
   # - github_owner (your GitHub username)
   # - aws_account_id, aws_region, pulumi_org, etc.
   ```

3) Set up the new project:
   ```bash
   cd your-project-name
   cp .env.example .env  # Edit with your actual credentials
   make bootstrap        # Creates GitHub repo, ECR, CI/CD setup
   make seed-stacks      # Initialize Pulumi stacks
   git push -u origin dev
   ```

### Option B: GitHub Template UI (Simple Copy)

This method creates a simple copy without variable substitution.

1) Go to https://github.com/MehdiZare/pantstack
2) Click "Use this template" → "Create a new repository"
3) Clone your new repository
4) Update `.env` file with your values (replace any remaining `{{ cookiecutter.* }}` placeholders)
5) Run setup commands:
   ```bash
   make bootstrap
   make seed-stacks
   git push -u origin dev
   ```

### Option C: Local Template

If you have the template locally:
```bash
make new-project  # Interactive prompts for all values
```

## Commands You’ll Use Often

- `make new-service S=<name>` — scaffold a new layered service under `services/<name>`
- `make mod-s S=web` — test and package a service
- `make svc-stack-up S=web ENV=test` — deploy a service stack
- `make svc-stack-outputs S=web ENV=test` — show stack outputs
- `make gha-deploy M=web ENV=prod` — trigger deploy workflow

Note: Pants is installed via the official bootstrap script. Local targets use `./pants`.

## Versioning & Promotion

- Dev merges → prereleases (`1.2.0-dev.3`) + deploy to test
- Dev→main PR → Pulumi preview only (dry run)
- Main merges → stable releases (`1.2.0`) + deploy to prod
- See `VERSIONING.md` for PR title format and label overrides

## Architecture

- Services live under `services/<svc>` with layered folders:
  - `app/{api,worker}` — FastAPI routers and workers
  - `domain/{models,services,ports}` — business logic and interfaces only
  - `adapters/{repositories,clients}` — concrete adapters (DynamoDB, EventBridge, S3, SQS, httpx)
  - `public/` — facades for cross-service access and DI providers
  - `infra/pulumi/` — ECS/Fargate and supporting AWS infra
  - `tests/{unit,integration,e2e}` — tests (prefer fast unit tests)
- Shared libs live under `stack/*`:
  - `stack/libs/shared` (logging, settings, aws client)
  - `stack/events` (event contracts)
  - `stack/infra/components` (ECS HTTP/Worker, Redis components)
  - `stack/agents` (agent runner stub)
  - Foundation infra: `stack/infra/foundation` (shared VPC, ECR, GH setup)

## Local Development (LocalStack)

Spin up AWS mocks and run services locally:

- `make dev-up` — start LocalStack (S3, SQS, DynamoDB) on `http://localhost:4566` and Redis on 6379
- `make dev-api-s S=web` — run the web API locally
- `make dev-worker-s S=agent` — run the agent worker locally
- `make dev-down` — stop LocalStack

Notes:
- When `LOCALSTACK=true`, adapters auto‑configure to LocalStack and create queues/buckets/tables if missing.

## Template vs. Generated Projects

- This repository is a template. CI jobs that deploy are disabled here by default via guards.
- In generated projects, leave `TEMPLATE_REPO_SLUG` unset so deploy/preview workflows run normally.

## First-time Checklist

- Read and follow `SETUP_CHECKLIST.md`
- For Pulumi Cloud Free, set `PULUMI_ORG` to your username.
- Run `make bootstrap` and then `make seed-stacks`.

See `AGENTS.md` for an agents playbook covering structure, commands, and reusable components.
