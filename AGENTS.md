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
