#!/usr/bin/env bash
set -euo pipefail

if [ "${M:-}" = "" ]; then
  echo "Usage: M=<module_name> [TYPE=http-api|worker] ./scripts/new_module.sh" >&2
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

if [ "$TYPE" = "http-api" ]; then
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

elif [ "$TYPE" = "worker" ]; then
  mkdir -p "$BASE/backend/worker"
  cat >> "$BASE/BUILD" << EOF

pex_binary(
    name="${LOWER}_worker_pex",
    entry_point="modules.${LOWER}.backend.worker.run:main",
    dependencies=[":${LOWER}_core"],
)

docker_image(name="${LOWER}_worker_image", dependencies=[":${LOWER}_worker_pex"], version_tags=["latest"])
EOF

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
  echo "Unsupported TYPE: $TYPE (supported: http-api, worker)" >&2
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

if [ "$TYPE" = "http-api" ]; then
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
else
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

if [ "$TYPE" = "http-api" ]; then
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
  if [ "$TYPE" = "http-api" ]; then
    sed -i.bak "/^\[python.resolves\]/a ${LOWER}_core   = \"lockfiles/${LOWER}_core.lock\"\n${LOWER}_api    = \"lockfiles/${LOWER}_api.lock\"" pants.toml && rm -f pants.toml.bak
  else
    sed -i.bak "/^\[python.resolves\]/a ${LOWER}_core   = \"lockfiles/${LOWER}_core.lock\"" pants.toml && rm -f pants.toml.bak
  fi
fi

echo "Module $LOWER scaffolded. Run: ./pants generate-lockfiles"
