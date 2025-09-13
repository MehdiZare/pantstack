# API Module (Demo)

This module showcases the baseline patterns:

- FastAPI service with `/healthz`, `/test-event` and `/test-event/{id}`.
- Asynchronous event backbone via SQS + S3 and an ECS Fargate worker.
- End-to-end CI/CD: build, deploy (test/prod), PR preview stacks, and verification.

## Endpoints

- `GET /healthz` → `{ "status": "ok" }`
- `POST /test-event` → `{ "id": "<uuid>" }` enqueues a task.
- `GET /test-event/{id}` → `{ "id": ..., "status": "done", "payload": ... }` after ~30s.

## Quick Manual Test

Assuming the ALB DNS is `http://<alb_dns>`:

- Health:
  curl -s -i http://<alb_dns>/healthz

- Submit:
  curl -s -X POST -H 'content-type: application/json' \
    -d '{"payload":{"hello":"world"}}' http://<alb_dns>/test-event

- Poll (replace <id>):
  curl -s http://<alb_dns>/test-event/<id>

The worker sleeps 30 seconds to simulate processing, then writes a result JSON to S3. The API polls S3 for the result when you call the status URL.

## Infrastructure Overview

- SQS queue + DLQ for the async task.
- S3 bucket for status results.
- ECS Fargate service (ALB) for the API.
- ECS Fargate service for the queue worker.

Pulumi stack outputs include `alb_dns`, `queue_url`, and `status_bucket`.

## CI Verification

Workflows call `scripts/verify_http.sh` to:
- check `/healthz` returns 200
- submit a test event and poll for completion (max 150s)

Deployments depend on these checks passing.

