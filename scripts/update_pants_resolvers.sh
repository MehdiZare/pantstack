#!/usr/bin/env bash
set -euo pipefail

# Script to add new service resolvers to pants.toml
# Usage: ./scripts/update_pants_resolvers.sh <service_name>
#
# This script automatically adds the required Python resolvers
# for a new service to pants.toml configuration

SVC=${1:-}
if [ -z "$SVC" ]; then
  echo "Error: Service name is required" >&2
  echo "Usage: $0 <service_name>" >&2
  echo "" >&2
  echo "Example: $0 orders" >&2
  exit 1
fi

PANTS_TOML="pants.toml"

# Check if resolvers already exist
if grep -q "${SVC}_core" "$PANTS_TOML"; then
  echo "Resolvers for service '$SVC' already exist in pants.toml"
  exit 0
fi

# Create a temporary file
TMP_FILE=$(mktemp)

# Find the line with "# Entry point resolves" and insert before it
awk -v svc="$SVC" '
/^# Entry point resolves/ {
  print svc "_core = \"lockfiles/" svc "_core.lock\""
  print svc "_api = \"lockfiles/" svc "_api.lock\""
  print ""
}
{ print }
' "$PANTS_TOML" > "$TMP_FILE"

# Replace the original file
mv "$TMP_FILE" "$PANTS_TOML"

echo "Added resolvers for service '$SVC' to pants.toml"
echo "Remember to run: ./pants generate-lockfiles"
