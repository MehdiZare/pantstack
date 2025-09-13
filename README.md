# Pantstack

Pantstack is a batteries-included monorepo template for modular services with Pants, FastAPI, Pulumi on AWS, and GitHub Actions.

- True module independence (per-module infra, packaging, and tests)
- Safe cross-module reuse via public facades and optional HTTP SDKs
- Single ECR per project; image tags encode module + branch + version
- CI/CD for lint, typecheck, tests, package, deploy, and PR preview stacks
- Pulumi Cloud (Free) backend; optional ESC (Environments) integration

## Quick Start (Template Author)

1) Publish this repository to GitHub and mark it as a Template:
   - Set `GITHUB_OWNER` and desired `GITHUB_REPO` (template name)
   - Run: `make pre-commit-install`
   - Run: `./scripts/publish_template.sh` (or do it in the GitHub UI)

2) Seed labels for semantic versioning (if not using publish_template.sh):
   - Actions → Run `labels-seed` workflow once.

## Create a New Project from the Template

Option A (recommended): Cookiecutter + Cruft

- `pipx install cookiecutter cruft` (or `pip install --user ...`)
- `cruft create gh:${GITHUB_OWNER}/${GITHUB_REPO:-pantstack}` and answer prompts
- In the new repo:
  - `cp .env.example .env` and fill values
  - `make bootstrap` (creates GitHub project repo, ECR, CI IAM, repo vars/secrets)
  - `make seed-stacks` (init test/prod stacks in Pulumi Cloud)
  - Optional: `make esc-init` and `make esc-attach M=api ENV=test`
  - Push to `dev` and open a PR; CI deploys test and verifies.

Option B: GitHub Template (UI)

- Click “Use this template”, then clone your repo.
- Fill `.env` and run `make bootstrap` and `make seed-stacks`.
- (Cookiecutter placeholders exist only in `.env.example` so this path works too.)

## Commands You’ll Use Often

- `make new-module M=orders` — scaffold a new module
- `make mod M=api` — test and package a module
- `make stack-up M=api ENV=test` — apply a stack locally
- `make stack-verify M=api ENV=test` — E2E verify
- `make gha-deploy M=api ENV=prod` — trigger deploy workflow

## Versioning & Promotion

- Dev merges → prereleases (`1.2.0-dev.3`) + deploy to test
- Dev→main PR → Pulumi preview only (dry run)
- Main merges → stable releases (`1.2.0`) + deploy to prod
- See `VERSIONING.md` for PR title format and label overrides

## Architecture

- See `modules/api` for a demo FastAPI + SQS worker and its Pulumi infra.
- Foundation infra (template bootstrap): `platform/infra/foundation` via Pulumi.
- Shared libs under `platform/libs/shared` and `platform/events`.

## First-time Checklist

- Read and follow `SETUP_CHECKLIST.md`
- For Pulumi Cloud Free, set `PULUMI_ORG` to your username.
- Run `make bootstrap` and then `make seed-stacks`.
