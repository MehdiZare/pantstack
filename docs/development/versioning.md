# Versioning & Promotion

This repo uses Conventional Commits and semantic-release to automate versioning, changelogs, and image tags.

- Branch policy:
  - `dev`: prereleases (e.g., `1.4.0-dev.3`)
  - `main`: stable releases (e.g., `1.4.0`)
- PR title check: Conventional Commit format is enforced for PRs. You can override with labels.
- Images are tagged with both branch/SHA and semantic version for easy rollback.

## Conventional Commit Examples

- `feat(api): add /users/{id}` → minor bump
- `fix(api): handle 404 correctly` → patch bump
- `perf(worker): improve SQS batch size` → patch bump
- `refactor(auth): simplify dto mapping` → no bump (unless breaking)
- `feat!: change public contract` → major bump (note the bang)

See: https://www.conventionalcommits.org/

## Release Labels (Optional Overrides)

If a PR title cannot follow the format, apply exactly one label:

- `release:major`
- `release:minor`
- `release:patch`
- `release:skip` (no version/release)

The PR title linter allows these labels as an override.

## What Gets Released

- On merge to `dev`:
  - semantic-release computes next prerelease, updates `CHANGELOG.md`, creates a GitHub prerelease.
  - CI publishes images tagged:
    - Branch/SHA: `${module}-dev-<sha>` and `${module}-worker-dev-<sha>`
    - Semantic: `${module}-v<prerelease>` and `${module}-worker-v<prerelease>`
  - Pulumi deploys test stacks and runs end-to-end verification.

- On merge to `main`:
  - semantic-release computes next stable version, updates `CHANGELOG.md`, creates a GitHub release.
  - CI publishes images tagged:
    - Branch/SHA: `${module}-main-<sha>` and `${module}-worker-main-<sha>`
    - Semantic: `${module}-v<version>` and `${module}-worker-v<version>`
  - Pulumi deploys prod stacks and runs verification.

## Promotion Flow

1. Feature branch → PR to `dev` (CI builds, deploys preview PR stacks, verifies).
2. Merge to `dev` (prerelease + deploy to test).
3. PR from `dev` → `main` (Pulumi preview only; dry run).
4. Merge to `main` (stable release + deploy to prod).

## Where It’s Wired

- PR title lint: `.github/workflows/semantic-pr.yml`
- Versioning config: `.releaserc.json`
- Dev auto-deploy: `.github/workflows/auto-deploy-dev.yml`
- Main auto-deploy: `.github/workflows/auto-deploy-main.yml`
- Changelog: `CHANGELOG.md` (auto-updated)

## Notes

- Prefer squash merges so the final commit message matches the PR title.
- Use `release:skip` for docs-only/infra-noop changes to avoid version bumps.
- All version and deploy steps run only after tests and runtime verification pass.

