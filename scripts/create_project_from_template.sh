#!/usr/bin/env bash
set -euo pipefail

# Creates a new project from this template using Cruft (Cookiecutter under the hood),
# bootstraps foundation, and seeds stacks.

if [ -z "${GITHUB_OWNER:-}" ] || [ -z "${TEMPLATE_REPO:-}" ]; then
  echo "Set GITHUB_OWNER and TEMPLATE_REPO env vars (template source)." >&2
  echo "Example: GITHUB_OWNER=you TEMPLATE_REPO=mono-template ./scripts/create_project_from_template.sh" >&2
  exit 1
fi

if ! command -v cruft >/dev/null 2>&1; then
  echo "Install cruft: pipx install cruft (or pip install --user cruft)" >&2
  exit 1
fi

echo "==> Rendering project via Cruft"
cruft create -y "gh:$GITHUB_OWNER/$TEMPLATE_REPO"

echo "==> Finding newly created directory"
dir=$(ls -td */ | head -n1)
dir=${dir%/}
echo "Project directory: $dir"

echo "==> Next steps"
cat <<TXT
cd $dir
cp .env.example .env  # fill values
make bootstrap        # creates GitHub project repo, seeds labels, ECR, CI IAM, secrets/vars
make seed-stacks      # initializes test/prod stacks in Pulumi Cloud
git push -u origin dev
TXT

