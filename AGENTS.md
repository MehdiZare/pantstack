# Repository Guidelines

## Project Structure & Services
- Monorepo with Pants (Python 3.12). Services live under `services/<name>` (layered: app/domain/adapters/public/infra/tests).
- Typical layout: `app/{api,worker}`, `domain/{models,services,ports}`, `adapters/{repositories,clients}`, `public/`, `infra/pulumi`, and `tests/{unit,integration,e2e}`.
- Shared code under `stack/libs`, `stack/events`, and `stack/infra/components`. Third‑party reqs in `3rdparty/python`; resolves in `pants.toml` and lockfiles under `lockfiles/`.

## Build, Test, and Dev Commands
- `make boot` — install Pants locally.
- `make fmt` — format via Black/isort (Pants).
- `make lint` — Flake8 + mypy typecheck.
- `make test` — run all tests.
- `make package` — build Docker images for all services.
- `make mod-s S=web` — test + package a single service.
- `make dev-up` / `make dev-down` — start/stop LocalStack + Redis.
- `make dev-api-s S=<svc>` / `make dev-worker-s S=<svc>` — run service API/worker locally.
- Direct Pants: `pants fmt ::`, `pants lint ::`, `pants test ::`, `pants package services/**:*image`.

- Python only; Pants interpreter constraint `==3.12.*` (see `pants.toml`).
- Formatting: Black; Imports: isort; Lint: Flake8 (line length 100; ignores E203,W503).
- Types: mypy via Pants; add annotations for public APIs.
- Cross‑service imports: avoid reaching into other services’ internals. Use `public` facades. Enforced by `flake8-import-restrictions`.
- Naming: packages `snake_case`; binaries/images use Pants targets (see `BUILD`).

## Testing Guidelines
- Place tests in `services/<name>/tests/{unit,integration,e2e}` inside each service.
- Name tests `test_*.py`; prefer fast, isolated unit tests. Integration/E2E may use Pulumi outputs where applicable.
- Run: `make test` or `pants test services/<name>/::`. Add dependencies in the service `BUILD` file.

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

## Service Scaffolding
- Create services: `make new-service S=<name>`.
- Scaffolds add BUILD targets, per-service resolves, and Pulumi boilerplate.

## Infra Components (Pulumi)
- Reusable ECS: `EcsHttpService` and `EcsWorkerService` (sidecar‑ready via `with_sidecar_redis` and `additional_containers`).
- Redis: `RedisService` (ECS/Fargate + internal NLB) for demo broker needs.
- Shared VPC exported by foundation stack; services can fetch `vpc_id`/`public_subnet_ids` via StackReference when available. Override with `VPC_ID`/`SUBNET_IDS` for ad‑hoc runs.

## Coding Style & Tests
- Black, isort, Flake8 (100 cols, E203/W503 ignored). mypy via Pants.
- Test layout: `backend/tests/{unit,integration,e2e}`; name files `test_*.py`. Run with `./pants test ::`.

## CI & PRs
- CI runs fmt, pre-commit, lint, typecheck, tests, and packaging of service images. Packaging/deploy steps are gated off in the template repo.
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
