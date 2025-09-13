#!/usr/bin/env bash
set -euo pipefail

if [ "${M:-}" = "" ]; then
  echo "Usage: M=<module_name> ./scripts/new_module.sh" >&2
  exit 1
fi

MOD="$M"
LOWER="$MOD"

BASE="modules/$LOWER"
echo "Scaffolding module at $BASE"
mkdir -p "$BASE/backend/api" "$BASE/backend/service" "$BASE/backend/schemas" "$BASE/backend/public" \
         "$BASE/backend/worker" "$BASE/backend/tests/unit" "$BASE/infrastructure"

cat > "$BASE/BUILD" << EOF
python_sources(
    name="${LOWER}_core",
    sources=["backend/{service,worker,schemas,public}/**/*.py"],
    resolve="${LOWER}_core",
    dependencies=["platform/libs/shared", "3rdparty/python:${LOWER}_core_reqs"],
)

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

pex_binary(
    name="${LOWER}_worker_pex",
    entry_point="modules.${LOWER}.backend.worker.run:main",
    dependencies=[":${LOWER}_core"],
)

docker_image(name="${LOWER}_image", dependencies=[":${LOWER}_api_pex"], version_tags=["latest"])
docker_image(name="${LOWER}_worker_image", dependencies=[":${LOWER}_worker_pex"], version_tags=["latest"])

python_tests(name="unit", sources=["backend/tests/unit/**/*.py"], resolve="tests", dependencies=[":${LOWER}_core"])
EOF

cat > "$BASE/backend/api/main.py" << 'PY'
from fastapi import FastAPI
from platform.libs.shared.logging import get_logger


log = get_logger("mod.api")
app = FastAPI()


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


def run() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
PY

cat > "$BASE/backend/worker/run.py" << 'PY'
def main() -> None:
    # implement your worker here
    pass

if __name__ == "__main__":
    main()
PY

cat > "$BASE/backend/schemas/__init__.py" << 'PY'
"""Pydantic models for public contracts."""
PY

cat > "$BASE/backend/public/__init__.py" << 'PY'
# Export stable facades here.
PY

cat > "$BASE/backend/service/__init__.py" << 'PY'
"""Business logic for the module."""
PY

cat > "$BASE/backend/tests/unit/test_health.py" << 'PY'
def test_placeholder():
    assert True
PY

cat > "$BASE/infrastructure/Pulumi.yaml" << 'YAML'
name: ${LOWER}
runtime:
  name: python
YAML

cat > "$BASE/infrastructure/requirements.txt" << 'REQ'
pulumi>=3.0.0
pulumi-aws>=6.0.0
REQ

cat > "$BASE/infrastructure/__main__.py" << 'PY'
import os
import pulumi
import pulumi_aws as aws


PROJECT_SLUG = os.getenv("PROJECT_SLUG", "mono-template")
AWS_REGION = os.getenv("AWS_REGION", "eu-west-2")
AWS_ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID", "")

MODULE = os.getenv("MODULE", "${LOWER}")

BRANCH = os.getenv("GITHUB_REF_NAME", "dev")
SHORT_SHA = (os.getenv("GITHUB_SHA", "") or "dev")[:7]
ECR_REPO = os.getenv("ECR_REPOSITORY", PROJECT_SLUG)
ECR_BASE = f"{AWS_ACCOUNT_ID}.dkr.ecr.{AWS_REGION}.amazonaws.com/{ECR_REPO}"

image_tag_api = f"{ECR_BASE}:{MODULE}-{BRANCH}-{SHORT_SHA}"

# Minimal placeholder stack
pulumi.export("image", image_tag_api)
PY

# Add 3rdparty requirements and resolves
echo "Appending 3rdparty requirements and resolves"
cat >> 3rdparty/python/BUILD << EOF

python_requirements(
    name="${LOWER}_core_reqs",
    source="requirements-${LOWER}-core.txt",
    resolve="${LOWER}_core",
)

python_requirements(
    name="${LOWER}_api_reqs",
    source="requirements-${LOWER}-api.txt",
    resolve="${LOWER}_api",
)
EOF

cat > 3rdparty/python/requirements-${LOWER}-core.txt << 'REQ'
pydantic>=2,<3
REQ

cat > 3rdparty/python/requirements-${LOWER}-api.txt << 'REQ'
fastapi>=0.111,<1
uvicorn[standard]>=0.30,<1
pydantic>=2,<3
REQ

echo "Adding resolves to pants.toml (if missing)"
grep -q "^${LOWER}_core\s*=\s*\"lockfiles/${LOWER}_core.lock\"" pants.toml || \
  sed -i.bak "/^\[python.resolves\]/a ${LOWER}_core   = \"lockfiles/${LOWER}_core.lock\"\n${LOWER}_api    = \"lockfiles/${LOWER}_api.lock\"" pants.toml && rm -f pants.toml.bak

echo "Module $LOWER scaffolded. Run: pants generate-lockfiles"

