#!/usr/bin/env bash
set -euo pipefail

# Ensure Pulumi CLI
if ! command -v pulumi >/dev/null 2>&1; then
  echo "Pulumi CLI not found in PATH. Please install it or run bootstrap." >&2
  exit 1
fi

# Load .env if present
if [ -f .env ]; then
  # shellcheck disable=SC2046
  export $(grep -v '^#' .env | xargs -I {} echo {})
fi

if [ -z "${PULUMI_ORG:-}" ]; then
  echo "PULUMI_ORG env var is required." >&2
  exit 1
fi

PROJECT_SLUG=${PROJECT_SLUG:-mono-template}
AWS_REGION=${AWS_REGION:-eu-west-2}
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID:-}

echo "==> Seeding module stacks in org: $PULUMI_ORG"

for infra in modules/*/infrastructure; do
  [ -d "$infra" ] || continue
  mod=$(basename "$(dirname "$infra")")
  for env in test prod; do
    stack="$PULUMI_ORG/$mod/$env"
    echo "-- $mod ($env)"
    pulumi -C "$infra" stack select "$stack" >/dev/null 2>&1 || pulumi -C "$infra" stack init "$stack"
    # Set common stack tags
    pulumi -C "$infra" stack tag set project "$PROJECT_SLUG" --stack "$stack" || true
    pulumi -C "$infra" stack tag set module "$mod" --stack "$stack" || true
    pulumi -C "$infra" stack tag set env "$env" --stack "$stack" || true
    # Optionally set shared config (aws:region) for future use
    pulumi -C "$infra" config set aws:region "$AWS_REGION" --stack "$stack" || true
    echo "   Pulumi stack: https://app.pulumi.com/$PULUMI_ORG/$mod/$env"
  done
done

echo "Pulumi stack seeding complete."
