#!/usr/bin/env bash
set -euo pipefail

# Publishes the current repo to GitHub and marks it as a template.
# Requires: GITHUB_TOKEN (PAT), GITHUB_OWNER, GITHUB_REPO

if [ -f .env ]; then
  # shellcheck disable=SC2046
  export $(grep -v '^#' .env | xargs -I {} echo {})
fi

if [ -z "${GITHUB_TOKEN:-}" ] && command -v gh >/dev/null 2>&1; then
  GITHUB_TOKEN=$(gh auth token 2>/dev/null || true)
  export GITHUB_TOKEN
fi

if [ -z "${GITHUB_TOKEN:-}" ] || [ -z "${GITHUB_OWNER:-}" ] || [ -z "${GITHUB_REPO:-}" ]; then
  echo "Set GITHUB_OWNER and GITHUB_REPO. For auth, either set GITHUB_TOKEN or run 'gh auth login' (we'll use 'gh auth token')." >&2
  exit 1
fi

remote_url="https://github.com/$GITHUB_OWNER/$GITHUB_REPO.git"

echo "==> Creating repo: $GITHUB_OWNER/$GITHUB_REPO (if not exists)"
code=$(curl -s -o /dev/null -w '%{http_code}' -H "Authorization: token $GITHUB_TOKEN" "https://api.github.com/repos/$GITHUB_OWNER/$GITHUB_REPO")
if [ "$code" != "200" ]; then
  curl -s -X POST \
    -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github+json" \
    "https://api.github.com/user/repos" \
    -d "{\"name\":\"$GITHUB_REPO\",\"private\":false,\"description\":\"Mono template\"}" >/dev/null
fi

echo "==> Pushing current repository"
git init >/dev/null 2>&1 || true
git remote remove origin >/dev/null 2>&1 || true
git remote add origin "$remote_url" || true
git fetch origin >/dev/null 2>&1 || true

if ! git show-ref --verify --quiet refs/heads/dev; then
  git checkout -b dev
else
  git checkout dev
fi
git add -A
git commit -m "chore: initial template" >/dev/null 2>&1 || true
git push -u origin dev

if ! git show-ref --verify --quiet refs/heads/main; then
  git branch main
fi
git push origin main || true

echo "==> Marking repo as template and setting default branch to dev"
curl -s -X PATCH \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$GITHUB_OWNER/$GITHUB_REPO" \
  -d '{"is_template":true,"default_branch":"dev"}' >/dev/null

echo "==> Setting repository topics and description"
curl -s -X PATCH \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$GITHUB_OWNER/$GITHUB_REPO" \
  -d '{
    "description": "Pantstack: Pants + Pulumi AWS monorepo template (FastAPI, CI/CD, PR previews)",
    "has_issues": true,
    "has_projects": false,
    "has_wiki": false
  }' >/dev/null

curl -s -X PUT \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$GITHUB_OWNER/$GITHUB_REPO/topics" \
  -d '{"names":["pantstack","monorepo","pants","pulumi","aws","template","fastapi","python","infrastructure-as-code"]}' >/dev/null

echo "Template published: $remote_url"
