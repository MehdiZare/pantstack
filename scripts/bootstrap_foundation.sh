#!/usr/bin/env bash
set -euo pipefail

# Load .env if present
if [ -f .env ]; then
  echo "Loading .env"
  # shellcheck disable=SC2046
  export $(grep -v '^#' .env | xargs -I {} echo {})
fi

prompt() {
  local var=$1; local msg=$2; local def=${3:-}
  if [ -z "${!var:-}" ]; then
    read -r -p "$msg${def:+ [$def]}: " input
    export "$var"="${input:-$def}"
  fi
}

prompt PROJECT_SLUG "Project slug (kebab-case)" "mono-template"
prompt GITHUB_OWNER "GitHub owner (user/org)"
prompt GITHUB_REPO "GitHub repo name" "$PROJECT_SLUG"
prompt GITHUB_VISIBILITY "Repo visibility (private/public)" "private"
prompt AWS_ACCOUNT_ID "AWS Account ID"
prompt AWS_REGION "AWS Region" "eu-west-2"
prompt PULUMI_ORG "Pulumi org"

if [ -z "${GITHUB_TOKEN:-}" ] && command -v gh >/dev/null 2>&1; then
  GITHUB_TOKEN=$(gh auth token 2>/dev/null || true)
  export GITHUB_TOKEN
fi
if [ -z "${GITHUB_TOKEN:-}" ]; then
  echo "GITHUB_TOKEN not set. Export a PAT or run 'gh auth login' so we can use 'gh auth token'." >&2
  exit 1
fi
if [ -z "${PULUMI_ACCESS_TOKEN:-}" ]; then
  echo "PULUMI_ACCESS_TOKEN not set. Please export it." >&2
  exit 1
fi

echo "==> Installing Pulumi CLI and Python deps"
if ! command -v pulumi >/dev/null 2>&1; then
  curl -fsSL https://get.pulumi.com | sh
  export PATH="$HOME/.pulumi/bin:$PATH"
fi
python3 -m venv .venv-foundation >/dev/null 2>&1 || true
. .venv-foundation/bin/activate
pip -q install -r platform/infra/foundation/requirements.txt

echo "==> Initializing Pulumi stack"
pushd platform/infra/foundation >/dev/null
STACK_NAME="$PULUMI_ORG/${PROJECT_SLUG}-foundation"
pulumi stack select "$STACK_NAME" || pulumi stack init "$STACK_NAME"

echo "==> Running Pulumi up (foundation)"
pulumi up --yes \
  --stack "$STACK_NAME"

echo "==> Reading outputs"
REPO_FULL_NAME=$(pulumi stack output github_repo)
DEFAULT_BRANCH=$(pulumi stack output github_default_branch)
echo "Created repo: $REPO_FULL_NAME (default: $DEFAULT_BRANCH)"
popd >/dev/null

REMOTE_URL="https://github.com/$GITHUB_OWNER/$GITHUB_REPO.git"

echo "==> Configuring git remotes and branches"
git init >/dev/null 2>&1 || true
git remote remove origin >/dev/null 2>&1 || true
git remote add origin "$REMOTE_URL"

# Ensure branches exist locally
git fetch origin >/dev/null 2>&1 || true

if ! git show-ref --verify --quiet refs/heads/dev; then
  git checkout -b dev
else
  git checkout dev
fi

git add -A
git commit -m "chore: initial scaffold" >/dev/null 2>&1 || true
git push -u origin dev

# Create main and push
if ! git show-ref --verify --quiet refs/heads/main; then
  git branch main
fi
git push origin main || true

echo "==> Setting default branch to dev (via API)"
curl -s -X PATCH \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/$GITHUB_OWNER/$GITHUB_REPO \
  -d '{"default_branch":"dev"}' >/dev/null

echo "All set. Repo: $REMOTE_URL (default branch: dev)"

echo "==> Seeding release/versioning labels"
seed_label() {
  local name="$1" color="$2" desc="$3"
  # Check if label exists
  code=$(curl -s -o /dev/null -w '%{http_code}' \
    -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github+json" \
    "https://api.github.com/repos/$GITHUB_OWNER/$GITHUB_REPO/labels/$(python3 -c 'import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))' "$name")")
  if [ "$code" = "200" ]; then
    # Update to desired color/description
    curl -s -X PATCH \
      -H "Authorization: token $GITHUB_TOKEN" \
      -H "Accept: application/vnd.github+json" \
      "https://api.github.com/repos/$GITHUB_OWNER/$GITHUB_REPO/labels/$(python3 -c 'import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))' "$name")" \
      -d "{\"new_name\":\"$name\",\"color\":\"$color\",\"description\":\"$desc\"}" >/dev/null || true
  else
    # Create label
    curl -s -X POST \
      -H "Authorization: token $GITHUB_TOKEN" \
      -H "Accept: application/vnd.github+json" \
      "https://api.github.com/repos/$GITHUB_OWNER/$GITHUB_REPO/labels" \
      -d "{\"name\":\"$name\",\"color\":\"$color\",\"description\":\"$desc\"}" >/dev/null || true
  fi
}

seed_label "release:major" "b60205" "force major release"
seed_label "release:minor" "0e8a16" "force minor release"
seed_label "release:patch" "1d76db" "force patch release"
seed_label "release:skip"  "c5def5" "skip semantic release"

echo "Seeded labels for semantic versioning overrides."

echo "==> Seeding Pulumi stacks for modules (test/prod)"
./scripts/seed_pulumi.sh || echo "Pulumi seeding skipped or failed; you can rerun with make seed-stacks"
