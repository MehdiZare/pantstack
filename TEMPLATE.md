# Using This Template

## Generate a new repository

Option A (Cookiecutter + Cruft):

1) Install: `pipx install cookiecutter cruft` (or `pip install --user ...`).
2) Create project: `cruft create gh:YOUR_ORG/YOUR_TEMPLATE_REPO` and answer prompts.
3) In the new repo, copy `.env.example` to `.env` and fill values.
4) Run foundation: `./scripts/bootstrap_foundation.sh`.

Option B (GitHub Template):

1) Click “Use this template”, then clone your repo.
2) Fill `.env` and run `./scripts/bootstrap_foundation.sh`.

## Update existing projects from template

In the generated project (contains a `.cruft.json`):

    cruft update

Review and apply the proposed patch.

## Add a new module

    ./scripts/new_module.sh M=orders

This scaffolds `modules/orders` with backend (api/worker/service/schemas/public), infra, and BUILD targets.

