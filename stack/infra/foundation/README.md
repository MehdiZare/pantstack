# Foundation Layer

Creates the minimal, shared prerequisites for the project:

- GitHub repository (default branch `dev`, Actions enabled)
- Single AWS ECR repository named by `PROJECT_SLUG`
- IAM user for CI/CD (GitHub Free; static creds)
- Shared VPC with two public subnets (for ECS services)
- GitHub Actions secrets/variables for AWS, Pulumi, and stack refs

Inputs are taken from environment variables (see `.env.example`).

Usage via helper script:

    cp .env.example .env  # then edit values
    ./scripts/bootstrap_foundation.sh

After completion, the script sets the remote and pushes the current repo to `dev` and `main`. A separate workflow blocks direct pushes to `main`.

Outputs (used by modules):

- `vpc_id` — ID of the shared foundation VPC
- `public_subnet_ids` — list of two public subnet IDs
- `FOUNDATION_STACK` — added as a GitHub Actions variable for convenience
