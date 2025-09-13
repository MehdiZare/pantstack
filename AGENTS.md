# Repository Guidelines

## Project Structure & Modules
- Monorepo with Pants. Modules live under `modules/<name>`.
- Typical layout: `backend/{api,service,schemas,public,worker,tests/{unit,integration,e2e}}`, plus `infrastructure/` (Pulumi).
- Shared code under `platform/libs` and `platform/events`. Third‑party reqs in `3rdparty/python`. Pants lockfiles in `lockfiles/`.

## Build, Test, and Dev Commands
- `make boot` — install Pants locally.
- `make fmt` — format via Black/isort (Pants).
- `make lint` — Flake8 + mypy typecheck.
- `make test` — run all tests.
- `make package` — build Docker images for all modules.
- `make mod M=api` — test + package a single module.
- `make up` / `make down` — start/stop local stack via `docker compose`.
- Direct Pants: `pants fmt ::`, `pants lint ::`, `pants test ::`, `pants package modules/**:*image`.

## Coding Style & Conventions
- Python only; Pants interpreter constraint `==3.11.*` (see `pants.toml`).
- Formatting: Black; Imports: isort; Lint: Flake8 (line length 100; ignores E203,W503).
- Types: mypy via Pants; add annotations for public APIs.
- Cross‑module imports: avoid reaching into other modules’ internals. Use `backend/public` facades. Enforced by `flake8-import-restrictions`.
- Naming: packages `snake_case`; binaries/images use Pants targets (see `BUILD`).

## Testing Guidelines
- Place tests in `backend/tests/{unit,integration,e2e}` inside each module.
- Name tests `test_*.py`; prefer fast, isolated unit tests. Integration/E2E may use Pulumi outputs where applicable.
- Run: `make test` or `pants test modules/<name>/::`. Add dependencies in the module `BUILD` file.

## Commit & Pull Requests
- Conventional Commits recommended: `feat(auth): ...`, `fix(api): ...`.
- Feature work targets `dev`. Merges to `dev` create prereleases and deploy to test. `dev → main` performs preview, then stable release to prod (see `VERSIONING.md`).
- PRs must include: clear description, linked issue, and any runtime notes. For new modules, prefer `make gh-new-module-pr M=<name>`.

## Security & Configuration
- Copy `.env.example` to `.env` and fill required values before bootstrap.
- First‑time setup: `make pre-commit-install`, `make bootstrap`, then `make seed-stacks`.
- Optional Pulumi ESC: `make esc-init` and `make esc-attach M=<name> ENV=test`.
# Repository Guidelines

## Project Structure & Modules
- Monorepo with Pants (Python 3.12). Modules live under `modules/<name>` with `backend/{api,worker,service,schemas,public,tests}` and `infrastructure/` (Pulumi).
- Shared libs/components: `platform/libs` (logging, settings, aws), `platform/infra/components` (ECS HTTP/Worker, Redis), `platform/agents` (agent runner stub).
- Third‑party requirements live in `3rdparty/python`; resolves in `pants.toml` and lockfiles under `lockfiles/`.

## Build, Test, and Dev
- Format/Lint/Test: `./pants fmt ::`, `./pants lint ::`, `./pants typecheck ::`, `./pants test ::`.
- Generate locks: `./pants generate-lockfiles`. Package images: `./pants package modules/**:*image`.
- Local dev (LocalStack + Redis): `make dev-up`, `make dev-api M=admin`, `make dev-worker M=admin`, `make dev-celery-up`, `make dev-celery-worker`, `make dev-all-admin`, `make dev-down`.
- Env: copy `.env.example` → `.env`. For Strapi tests set `STRAPI_URL` and `STRAPI_TOKEN`.

## Module Scaffolding
- Create modules: `make new-module M=<name> TYPE=<kind>`.
- Supported TYPEs:
  - `http-api` — minimal FastAPI service.
  - `worker` — generic worker entrypoint.
  - `ui-celery` — web UI (form) that schedules Celery tasks and polls status.
  - `worker-celery` — Celery app/worker wrapping `platform.agents.runner.run_agent`.
  - `event-backend-redis` — infra-only Redis on ECS (demo broker).
- Scaffolds add BUILD targets, 3rd‑party reqs, resolves, and Pulumi boilerplate.

## Infra Components (Pulumi)
- Reusable ECS: `EcsHttpService` and `EcsWorkerService` (sidecar‑ready via `with_sidecar_redis` and `additional_containers`).
- Redis: `RedisService` (ECS/Fargate + internal NLB) for demo broker needs.
- Shared VPC exported by foundation stack; modules should fetch `vpc_id`/`public_subnet_ids` via Pulumi StackReference when available. Override with `VPC_ID`/`SUBNET_IDS` only for ad‑hoc runs.

## Coding Style & Tests
- Black, isort, Flake8 (100 cols, E203/W503 ignored). mypy via Pants.
- Test layout: `backend/tests/{unit,integration,e2e}`; name files `test_*.py`. Run with `./pants test ::`.

## CI & PRs
- CI runs fmt, pre-commit, lint, typecheck, and tests. Packaging/deploy steps are gated off in the template repo.
- Conventional Commits recommended; see `VERSIONING.md`. Open PRs to `dev`; releases flow to `main`.

## Starter Recipe
- Single-module (UI + Worker via Celery):
  1) `make new-module M=ui TYPE=ui-celery`
  2) `make dev-celery-up`
  3) In two terminals: `make dev-api M=ui` and `make dev-celery-worker M=ui`
  4) Open `http://localhost:8000/jobs/new` → submit a job → refresh status page.

- Split UI and Worker (optional):
  1) `make new-module M=ui TYPE=ui-celery`
  2) `make new-module M=jobs TYPE=worker-celery`
  3) Run `make dev-celery-up`, then `make dev-api M=ui` and `make dev-celery-worker M=jobs`
  4) Point the UI to the worker module’s Celery app if you separate (see generated `ui` code for import location).

- Event backend for cloud (optional):
  - `make new-module M=events TYPE=event-backend-redis` to scaffold a Redis broker on ECS; wire `CELERY_BROKER_URL` to the stack output.
