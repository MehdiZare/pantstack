# Setup Checklist

Use this quick checklist to initialize a new project from this template.

- Accounts & Tokens
  - Pulumi Cloud account created, `PULUMI_ACCESS_TOKEN` ready
  - AWS account id/region known; have IAM permissions locally
  - GitHub Personal Access Token (PAT) for repo creation (repo, workflow)

- Template Render
  - Render with Cookiecutter/Cruft (`cruft create gh:owner/template`)
  - Fill `.env` (see `.env.example`)

- Bootstrap
  - `make bootstrap` (creates GitHub repo, ECR, CI IAM, repo secrets/vars, dev/main branches)
  - Seeds versioning labels automatically
  - Optional: `make esc-init` to create shared Pulumi ESC environment
  - `make seed-stacks` (initializes test/prod stacks for all modules)

- First CI Run
  - Push to `dev` (or open PR to dev): CI builds, deploys test, verifies
  - Confirm outputs and PR comment URLs are reachable

- Day 2
  - Create feature module: `make gh-new-module-pr M=orders`
  - Promote via PR dev→main; verify preview plan; merge to deploy prod
