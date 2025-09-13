#!/usr/bin/env bash
set -euo pipefail

BASE_URL="$1"

echo "Verifying health endpoint at $BASE_URL/healthz"
code=$(curl -s -o /dev/null -w '%{http_code}' "$BASE_URL/healthz")
if [ "$code" != "200" ]; then
  echo "Health check failed with status: $code" >&2
  exit 1
fi

echo "Submitting test event"
resp=$(curl -s -X POST -H 'content-type: application/json' \
  -d '{"payload":{"hello":"world"}}' "$BASE_URL/test-event")
id=$(echo "$resp" | jq -r '.id // empty')
if [ -z "$id" ]; then
  echo "Failed to get correlation id from response: $resp" >&2
  exit 1
fi
echo "Correlation id: $id"

echo "Polling for result..."
deadline=$(( $(date +%s) + 150 ))
while true; do
  if [ $(date +%s) -ge $deadline ]; then
    echo "Timed out waiting for result" >&2
    exit 1
  fi
  out=$(curl -s "$BASE_URL/test-event/$id") || true
  status=$(echo "$out" | jq -r '.status // empty')
  if [ "$status" = "done" ]; then
    echo "Success: $out"
    break
  fi
  sleep 5
done
