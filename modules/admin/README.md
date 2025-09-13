# Admin Module (Demo)

Provides a small admin API to schedule long-running jobs and a worker to execute them (simulated agent runner).

- API endpoints:
  - `POST /admin/schedule` — body: `{ "job_type": "...", "params": { ... } }` → `{ "id": "<uuid>" }`
  - `GET /admin/jobs/{id}` — returns `{ status: pending|completed, ... }` from S3
- Worker consumes from SQS, calls `platform.agents.runner.run_agent`, writes results to S3.
- LocalStack support: with `LOCALSTACK=true`, queue/bucket are auto-created if missing.

## Local Development

- Start LocalStack: `make dev-up`
- Start everything: `make dev-all-admin`
- Or run individually:
  - API: `make dev-api M=admin`
  - Worker: `make dev-worker M=admin`
  - Scheduler: `make dev-scheduler M=admin`

Logs are written under `.dev/*.log` when using `dev-all-admin`.
