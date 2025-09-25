#!/usr/bin/env bash
set -euo pipefail

# Load .env if present
if [ -f .env ]; then
  # shellcheck disable=SC2046
  export $(grep -v '^#' .env | xargs -I {} echo {})
fi

PULUMI_ORG=${PULUMI_ORG:-}
ENV_NAME=${ESC_ENV_NAME:-shared}

if [ -z "$PULUMI_ORG" ]; then
  echo "PULUMI_ORG must be set in env or .env" >&2
  exit 1
fi

if ! command -v pulumi >/dev/null 2>&1; then
  echo "Pulumi CLI not found. Install via curl -fsSL https://get.pulumi.com | sh" >&2
  exit 1
fi

echo "==> Initializing ESC environment: $PULUMI_ORG/$ENV_NAME"
pulumi env init "$PULUMI_ORG/$ENV_NAME" >/dev/null 2>&1 || true

echo "==> Pushing values from pulumi/envs/shared.yaml"
pulumi env set -f pulumi/envs/shared.yaml -e "$PULUMI_ORG/$ENV_NAME"

echo "ESC environment ready: $PULUMI_ORG/$ENV_NAME"
