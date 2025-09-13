# Foundation Layer

Creates the minimal, shared prerequisites for the project:

- GitHub repository (default branch `dev`, Actions enabled)
- Single AWS ECR repository named by `PROJECT_SLUG`
- IAM user for CI/CD with minimal ECR push/pull permissions
- GitHub Actions secrets/variables for AWS and Pulumi

Inputs are taken from environment variables (see `.env.example`).

Usage via helper script:

    cp .env.example .env  # then edit values
    ./scripts/bootstrap_foundation.sh

After completion, the script sets the remote and pushes the current repo to `dev` and `main`. A separate workflow blocks direct pushes to `main`.

