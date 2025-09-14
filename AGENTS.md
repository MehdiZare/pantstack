# AGENTS Playbook

This repository is a Python 3.12 monorepo template scaffolded for fast service/module development with Pants, Pulumi, and reusable building blocks. Agents working in this repo must follow the conventions below to keep code consistent and CI green.

## Layout Overview
- Services: `services/<name>`
  - Layering: `app/{api,worker}`, `domain/{models,services,ports}`, `adapters/{repositories,clients}`, `public/`, `infra/pulumi`, `tests/{unit,integration,e2e}`.
- Modules: `modules/<name>`
  - Backend: `backend/{api,worker,service,schemas,public,tests}`; Infra: `infrastructure/` (Pulumi).
- Shared: `stack/libs`, `stack/events`, `stack/infra/components` (reusable Pulumi), and `platform/*` (libs/components/agents).
- Dependencies: third‑party reqs in `3rdparty/python`; constraints and resolves in `pants.toml`; lockfiles in `lockfiles/`.

## Tooling & Commands
- First‑time setup: `make pre-commit-install`, `make boot`, copy `.env.example` to `.env` and fill required values.
- Format/Lint/Typecheck/Tests:
  - `pants fmt ::`, `pants lint ::`, `pants check ::`, `pants test ::`
  - Or convenience: `make fmt`, `make lint`, `make test`.
- Package images: `pants package services/**:*image` or `pants package modules/**:*image`.
- Local dev (LocalStack + Redis): `make dev-up` / `make dev-down`.
  - Service dev: `make dev-api-s S=<svc>` and `make dev-worker-s S=<svc>`.
  - Module dev: `make dev-api M=<module>`, `make dev-worker M=<module>`, `make dev-celery-up`, `make dev-celery-worker`.

## Style, Types, and Imports
- Black + isort + Flake8 (100 cols; ignore E203/W503). mypy via Pants.
- Public APIs should be annotated; add minimal annotations in tests if mypy requests them.
- isort is configured to treat Pulumi packages as third‑party: `pulumi`, `pulumi_aws`, `pulumi_github`. Keep imports grouped stdlib → third‑party → first‑party. If isort rewrites in CI, commit the changes.
- Cross‑service boundaries: never import another service’s internals; only use its `public` facade. Enforced by flake8 import restrictions.

## Reusable Infra Components (Pulumi)
Found in `stack/infra/components` and consumable from `infra/pulumi` (services) or `infrastructure/` (modules):
- `EcsHttpService`: Fargate HTTP service behind an ALB. Inputs: `name`, `image`, `port`, `env`, optional `vpc_id`/`subnet_ids`. Outputs: `url`, `alb_dns`, `cluster_arn`, `service_arn`.
- `EcsWorkerService`: Fargate worker with optional `command`, `with_sidecar_redis`, `additional_containers`, and inline IAM policy for tasks.
- `RedisService`: Ephemeral Redis on Fargate + internal NLB for demos/dev.
- VPC discovery: if `vpc_id`/`subnet_ids` omitted and `PULUMI_ORG` is set, components read them from the foundation stack `${PULUMI_ORG}/${PROJECT_SLUG}-foundation` (override with `FOUNDATION_STACK`). Otherwise, pass network IDs explicitly.

Minimal example:
```
import os
import pulumi
import pulumi_aws as aws
from stack.infra.components.http_service import EcsHttpService

PROJECT_SLUG = os.getenv("PROJECT_SLUG", "mono-template")
AWS_REGION = os.getenv("AWS_REGION", "eu-west-2")
AWS_ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID", "")
BRANCH = os.getenv("GITHUB_REF_NAME", "dev")
SHORT_SHA = (os.getenv("GITHUB_SHA", "") or "dev")[:7]
ECR_REPO = os.getenv("ECR_REPOSITORY", PROJECT_SLUG)
ECR_BASE = f"{AWS_ACCOUNT_ID}.dkr.ecr.{AWS_REGION}.amazonaws.com/{ECR_REPO}"

svc = EcsHttpService(
    name="web-api",
    image=f"{ECR_BASE}:web-{BRANCH}-{SHORT_SHA}",
    port=8000,
    env={"SERVICE_NAME": "web"},
)
pulumi.export("url", svc.url)
```

## Create a New Project From This Template
1) Bootstrap
   - Clone this repo and create a new remote for your project.
   - Set env in `.env` (`PROJECT_SLUG`, `AWS_*`, `PULUMI_*`).
   - Run: `make pre-commit-install`, `make boot`, `make bootstrap`.
2) Choose structure
   - Service‑oriented: `make new-service S=<name>` (adds `services/<name>` with BUILD targets and Pulumi boilerplate).
   - Module‑oriented: `make new-module M=<name> TYPE=<ui-celery|worker-celery|event-backend-redis>`.
3) Implement app code
   - HTTP in `app/api`, workers in `app/worker`, domain logic in `domain`, adapters under `adapters`.
   - Expose a minimal `public/` facade for cross‑service consumption.
4) Wire infrastructure
   - Use the reusable components above; prefer foundation VPC autodiscovery.
5) Run locally
   - `make dev-up`; then `make dev-api-s S=<name>` / `make dev-worker-s S=<name>` (or module equivalents).
6) CI ready
   - `pants fmt :: && pants lint :: && pants check :: && pants test ::` must pass. If isort modifies imports, commit those changes.

Starter recipes:
- Single module (UI + Celery worker):
  - `make new-module M=ui TYPE=ui-celery`
  - `make dev-celery-up`; then `make dev-api M=ui` and `make dev-celery-worker M=ui`
  - Visit `http://localhost:8000/jobs/new` to submit a job and check status.
- Split UI and Worker:
  - `make new-module M=ui TYPE=ui-celery` and `make new-module M=jobs TYPE=worker-celery`
  - `make dev-celery-up`; then `make dev-api M=ui` and `make dev-celery-worker M=jobs`

## Dependency Management
- Add third‑party deps to `3rdparty/python` requirement targets; run `pants generate-lockfiles`.
- Add per‑service/module resolves and explicit `dependencies` in BUILD files as needed.
- If Pants warns about ambiguous owners (e.g., multiple resolves own `pydantic`), pin the desired target in `dependencies` or exclude others with `!`/`!!`.

## PR & Release Flow
- Work from `dev`; use Conventional Commits (e.g., `feat(auth): ...`, `fix(api): ...`).
- Merging to `dev` creates prereleases and deploys to test; `dev → main` performs preview then stable release (see `VERSIONING.md`).

## Agent Rules
- Keep changes minimal and within the existing structure; do not reach into other services beyond their `public` APIs.
- Use Pants goals to validate changes locally.
- Respect import order and add types for public APIs and tests as needed.
- Update this file when developer workflows or conventions change.
