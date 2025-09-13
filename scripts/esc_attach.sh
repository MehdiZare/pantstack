#!/usr/bin/env bash
set -euo pipefail

# Usage: M=api ENV=test ./scripts/esc_attach.sh [ESC_ENV_NAME]

if [ -f .env ]; then
  # shellcheck disable=SC2046
  export $(grep -v '^#' .env | xargs -I {} echo {})
fi

M=${M:-}
ENV=${ENV:-}
ESC_ENV_NAME=${1:-${ESC_ENV_NAME:-shared}}

if [ -z "$M" ] || [ -z "$ENV" ]; then
  echo "Usage: M=<module> ENV=<env> ./scripts/esc_attach.sh [ESC_ENV_NAME]" >&2
  exit 1
fi

if [ -z "${PULUMI_ORG:-}" ]; then
  echo "PULUMI_ORG must be set" >&2
  exit 1
fi

STACK="$PULUMI_ORG/$M/$ENV"
ENV_REF="$PULUMI_ORG/$ESC_ENV_NAME"

if ! command -v pulumi >/dev/null 2>&1; then
  echo "Pulumi CLI not found. Install via curl -fsSL https://get.pulumi.com | sh" >&2
  exit 1
fi

echo "==> Attaching ESC environment $ENV_REF to stack $STACK"
pulumi -C modules/$M/infrastructure stack select "$STACK" >/dev/null 2>&1 || pulumi -C modules/$M/infrastructure stack init "$STACK"

# Best-effort attachment. Newer Pulumi versions support stack environment attachment via CLI.
if pulumi -C modules/$M/infrastructure env ls >/dev/null 2>&1; then
  pulumi -C modules/$M/infrastructure env add "$ENV_REF" --stack "$STACK" || true
else
  echo "This Pulumi version may not support 'pulumi env' stack attachment. Storing reference in stack config as ESC_ENV=$ENV_REF"
  pulumi -C modules/$M/infrastructure config set ESC_ENV "$ENV_REF" --stack "$STACK"
fi

echo "Attached (or referenced) ESC environment for $STACK"
