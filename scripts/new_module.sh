#!/usr/bin/env bash
set -euo pipefail

if [ "${M:-}" = "" ]; then
  echo "Usage: M=<module_name> [TYPE=http-api|worker|ui-celery|worker-celery|event-backend-redis] ./scripts/new_module.sh" >&2
  exit 1
fi

TYPE="${TYPE:-http-api}"
MOD="$M"
LOWER="$MOD"
BASE="modules/$LOWER"

echo "Scaffolding module '$LOWER' of type '$TYPE' at $BASE"
mkdir -p "$BASE/backend/service" "$BASE/backend/schemas" "$BASE/backend/public" "$BASE/backend/tests/unit" "$BASE/infrastructure"

# Common BUILD: core library
cat > "$BASE/BUILD" << EOF
python_sources(
    name="${LOWER}_core",
    sources=["backend/{service,schemas,public}/**/*.py"],
    resolve="${LOWER}_core",
    dependencies=["platform/libs/shared", "3rdparty/python:${LOWER}_core_reqs"],
)

python_tests(name="unit", sources=["backend/tests/unit/**/*.py"], resolve="tests", dependencies=[":${LOWER}_core"])
EOF

if [ "$TYPE" = "http-api" ] || [ "$TYPE" = "ui-celery" ]; then
  mkdir -p "$BASE/backend/api"
  cat >> "$BASE/BUILD" << EOF

python_sources(
    name="${LOWER}_api_src",
    sources=["backend/api/**/*.py"],
    resolve="${LOWER}_api",
    dependencies=[":${LOWER}_core", "3rdparty/python:${LOWER}_api_reqs"],
)

pex_binary(
    name="${LOWER}_api_pex",
    entry_point="modules.${LOWER}.backend.api.main:run",
    dependencies=[":${LOWER}_api_src"],
)

docker_image(name="${LOWER}_image", dependencies=[":${LOWER}_api_pex"], version_tags=["latest"])
EOF

  cat > "$BASE/backend/api/main.py" << 'PY'
from fastapi import FastAPI
from platform.libs.shared.logging import get_logger
from platform.libs.shared.settings_pydantic import settings


log = get_logger("mod.api")
app = FastAPI(title=settings.service_name)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


def run() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
PY

  if [ "$TYPE" = "ui-celery" ]; then
    cat > "$BASE/backend/api/main.py" << EOF
import os
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from platform.libs.shared.logging import get_logger


log = get_logger("mod.ui")
app = FastAPI(title="${LOWER}-ui")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return '<meta http-equiv="refresh" content="0; url=/jobs/new" />'


@app.get("/jobs/new", response_class=HTMLResponse)
def new_job() -> str:
    return """
    <html><body style='font-family:sans-serif;max-width:720px;margin:2rem auto'>
      <h1>New Job</h1>
      <form method=post action='/jobs'>
        <label>Job Type <input name=job_type value='content.generate'/></label>
        <label>Title <input name=title placeholder='Title'/></label>
        <label>Topic <input name=topic placeholder='Topic'/></label>
        <button type=submit>Schedule</button>
      </form>
    </body></html>
    """


@app.post("/jobs")
def schedule(job_type: str = Form(...), title: str = Form(""), topic: str = Form("")):
    from modules.${LOWER}.backend.worker.celery_app import run_agent_task
    res = run_agent_task.delay(job_type, {"title": title, "topic": topic})
    return RedirectResponse(url=f"/jobs/{res.id}", status_code=303)


@app.get("/jobs/{task_id}", response_class=HTMLResponse)
def view(task_id: str) -> str:
    from modules.${LOWER}.backend.worker.celery_app import app as celery_app
    from celery.result import AsyncResult
    r = AsyncResult(task_id, app=celery_app)
    status = r.status.lower()
    return f"<html><body style='font-family:sans-serif;max-width:720px;margin:2rem auto'><h1>Job {task_id}</h1><p>Status: <b>{status}</b></p><a href='/jobs/{task_id}'>Refresh</a></body></html>"


def run() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF
  fi

elif [ "$TYPE" = "worker" ] || [ "$TYPE" = "worker-celery" ]; then
  mkdir -p "$BASE/backend/worker"
  cat >> "$BASE/BUILD" << EOF

pex_binary(
    name="${LOWER}_worker_pex",
    entry_point="modules.${LOWER}.backend.worker.run:main",
    dependencies=[":${LOWER}_core"],
)

docker_image(name="${LOWER}_worker_image", dependencies=[":${LOWER}_worker_pex"], version_tags=["latest"])
EOF

  if [ "$TYPE" = "worker" ]; then
  cat > "$BASE/backend/worker/run.py" << 'PY'
from platform.libs.shared.logging import get_logger
from platform.libs.shared.settings_pydantic import settings


log = get_logger("mod.worker")


def main() -> None:
    log.info("Worker starting", extra={"env": settings.env, "service": settings.service_name})
    # implement your worker here
    pass


if __name__ == "__main__":
    main()
PY
  else
  cat > "$BASE/backend/worker/celery_app.py" << 'PY'
import os
from celery import Celery
from platform.agents.runner import run_agent


broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
result_backend = os.getenv("CELERY_RESULT_BACKEND", broker_url)

app = Celery("${LOWER}", broker=broker_url, backend=result_backend)


@app.task(name="${LOWER}.run_agent")
def run_agent_task(job_type: str, params: dict) -> dict:
    return run_agent(job_type, params)
PY

  cat > "$BASE/backend/worker/celery_run.py" << 'PY'
def main() -> None:
    import sys
    from celery.bin.celery import main as celery_main

    sys.argv = ["celery", "-A", "modules.${LOWER}.backend.worker.celery_app", "worker", "-l", "info"]
    celery_main()


if __name__ == "__main__":
    main()
PY

  cat >> "$BASE/BUILD" << EOF

pex_binary(
    name="${LOWER}_celery_worker_pex",
    entry_point="modules.${LOWER}.backend.worker.celery_run:main",
    dependencies=[":${LOWER}_core"],
)

docker_image(name="${LOWER}_celery_worker_image", dependencies=[":${LOWER}_celery_worker_pex"], version_tags=["latest"])
EOF
  fi
else
  echo "Unsupported TYPE: $TYPE (supported: http-api, worker, ui-celery, worker-celery, event-backend-redis)" >&2
  exit 1
fi

# Common Python packages
cat > "$BASE/backend/schemas/__init__.py" << 'PY'
"""Pydantic models for public contracts."""
PY

cat > "$BASE/backend/public/__init__.py" << 'PY'
# Export stable facades here.
PY

cat > "$BASE/backend/service/__init__.py" << 'PY'
"""Business logic for the module."""
PY

cat > "$BASE/backend/tests/unit/test_placeholder.py" << 'PY'
def test_placeholder():
    assert True
PY

# Infrastructure
cat > "$BASE/infrastructure/Pulumi.yaml" << 'YAML'
name: ${LOWER}
runtime:
  name: python
YAML

cat > "$BASE/infrastructure/requirements.txt" << 'REQ'
pulumi>=3.0.0
pulumi-aws>=6.0.0
REQ

if [ "$TYPE" = "http-api" ] || [ "$TYPE" = "ui-celery" ]; then
  cat > "$BASE/infrastructure/__main__.py" << 'PY'
import os
import sys
import pathlib
import pulumi
sys.path.append(str(pathlib.Path(__file__).resolve().parents[3]))
from platform.infra.components.http_service import EcsHttpService

PROJECT_SLUG = os.getenv("PROJECT_SLUG", "mono-template")
AWS_REGION = os.getenv("AWS_REGION", "eu-west-2")
AWS_ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID", "")
MODULE = os.getenv("MODULE", "${LOWER}")

BRANCH = os.getenv("GITHUB_REF_NAME", "dev")
SHORT_SHA = (os.getenv("GITHUB_SHA", "") or "dev")[:7]
ECR_REPO = os.getenv("ECR_REPOSITORY", PROJECT_SLUG)
ECR_BASE = f"{AWS_ACCOUNT_ID}.dkr.ecr.{AWS_REGION}.amazonaws.com/{ECR_REPO}"

image = f"{ECR_BASE}:{MODULE}-{BRANCH}-{SHORT_SHA}"

svc = EcsHttpService(name=f"{MODULE}-api", image=image, port=8000, env={"SERVICE_NAME": MODULE})

pulumi.export("alb_dns", svc.alb_dns)
pulumi.export("url", svc.url)
PY
elif [ "$TYPE" = "worker" ] || [ "$TYPE" = "worker-celery" ]; then
  cat > "$BASE/infrastructure/__main__.py" << 'PY'
import os
import sys
import pathlib
import pulumi
sys.path.append(str(pathlib.Path(__file__).resolve().parents[3]))
from platform.infra.components.worker_service import EcsWorkerService

PROJECT_SLUG = os.getenv("PROJECT_SLUG", "mono-template")
AWS_REGION = os.getenv("AWS_REGION", "eu-west-2")
AWS_ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID", "")
MODULE = os.getenv("MODULE", "${LOWER}")

BRANCH = os.getenv("GITHUB_REF_NAME", "dev")
SHORT_SHA = (os.getenv("GITHUB_SHA", "") or "dev")[:7]
ECR_REPO = os.getenv("ECR_REPOSITORY", PROJECT_SLUG)
ECR_BASE = f"{AWS_ACCOUNT_ID}.dkr.ecr.{AWS_REGION}.amazonaws.com/{ECR_REPO}"

image = f"{ECR_BASE}:{MODULE}-worker-{BRANCH}-{SHORT_SHA}"

svc = EcsWorkerService(name=f"{MODULE}-worker", image=image, env={"SERVICE_NAME": MODULE})

pulumi.export("cluster", svc.cluster_arn)
pulumi.export("service", svc.service_arn)
PY
fi

if [ "$TYPE" = "event-backend-redis" ]; then
  cat > "$BASE/infrastructure/__main__.py" << 'PY'
import os
import sys
import pathlib
import pulumi
sys.path.append(str(pathlib.Path(__file__).resolve().parents[3]))
from platform.infra.components.redis_service import RedisService

PROJECT_SLUG = os.getenv("PROJECT_SLUG", "mono-template")
ref = pulumi.StackReference(f"{os.getenv('PULUMI_ORG')}/{PROJECT_SLUG}-foundation")
vpc_id = ref.get_output("vpc_id")
subnets = ref.get_output("public_subnet_ids")

svc = RedisService(name="redis", vpc_id=vpc_id, subnet_ids=subnets)
pulumi.export("endpoint", svc.endpoint)
PY
fi

# 3rdparty requirements/resolves
echo "Appending 3rdparty requirements and resolves"
cat >> 3rdparty/python/BUILD << EOF

python_requirements(
    name="${LOWER}_core_reqs",
    source="requirements-${LOWER}-core.txt",
    resolve="${LOWER}_core",
)
EOF

cat > 3rdparty/python/requirements-${LOWER}-core.txt << 'REQ'
pydantic>=2,<3
REQ

if [ "$TYPE" = "worker-celery" ] || [ "$TYPE" = "ui-celery" ]; then
  echo "celery[redis]>=5.3,<6" >> 3rdparty/python/requirements-${LOWER}-core.txt
fi

if [ "$TYPE" = "http-api" ] || [ "$TYPE" = "ui-celery" ]; then
  cat >> 3rdparty/python/BUILD << EOF

python_requirements(
    name="${LOWER}_api_reqs",
    source="requirements-${LOWER}-api.txt",
    resolve="${LOWER}_api",
)
EOF

  cat > 3rdparty/python/requirements-${LOWER}-api.txt << 'REQ'
fastapi>=0.111,<1
uvicorn[standard]>=0.30,<1
pydantic>=2,<3
REQ
fi

echo "Adding resolves to pants.toml (if missing)"
if ! grep -q "^${LOWER}_core\s*=\s*\"lockfiles/${LOWER}_core.lock\"" pants.toml; then
if [ "$TYPE" = "http-api" ] || [ "$TYPE" = "ui-celery" ]; then
    sed -i.bak "/^\[python.resolves\]/a ${LOWER}_core   = \"lockfiles/${LOWER}_core.lock\"\n${LOWER}_api    = \"lockfiles/${LOWER}_api.lock\"" pants.toml && rm -f pants.toml.bak
  else
    sed -i.bak "/^\[python.resolves\]/a ${LOWER}_core   = \"lockfiles/${LOWER}_core.lock\"" pants.toml && rm -f pants.toml.bak
  fi
fi

echo "Module $LOWER scaffolded. Run: ./pants generate-lockfiles"
