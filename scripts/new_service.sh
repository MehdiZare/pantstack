#!/usr/bin/env bash
set -euo pipefail

SVC=${S:-${1:-}}
if [ -z "$SVC" ]; then
  echo "Usage: S=<name> scripts/new_service.sh" >&2
  exit 1
fi
base="services/$SVC"
if [ -d "$base" ]; then
  echo "Service '$SVC' already exists at $base"
  exit 0
fi

echo "Scaffolding service at $base"
mkdir -p "$base"/app/api "$base"/app/worker "$base"/domain/models "$base"/domain/services "$base"/domain/ports "$base"/adapters/repositories "$base"/public "$base"/infra/pulumi "$base"/tests/unit

cat > "$base"/BUILD << 'EOF'
python_sources(
    name="core",
    sources=["domain/**/*.py", "adapters/**/*.py", "public/**/*.py"],
    resolve="platform_core",
    dependencies=["stack/libs/shared", "3rdparty/python:platform_core_reqs"],
)

python_sources(
    name="api_src",
    sources=["app/api/**/*.py"],
    resolve="platform_core",
    dependencies=[":core"],
)

python_sources(
    name="worker_src",
    sources=["app/worker/**/*.py"],
    resolve="platform_core",
    dependencies=[":core"],
)

pex_binary(name="api_pex", entry_point="services.${name}.app.api.main:run", dependencies=[":api_src"])  # type: ignore[name-defined]
pex_binary(name="worker_pex", entry_point="services.${name}.app.worker.run:main", dependencies=[":worker_src"])  # type: ignore[name-defined]

docker_image(name="image", dependencies=[":api_pex"], image_tags=["latest"])
docker_image(name="worker_image", dependencies=[":worker_pex"], image_tags=["latest"])

python_tests(name="unit", sources=["tests/unit/**/*.py"], resolve="tests", dependencies=[":core", ":api_src", ":worker_src"])
EOF

sed -i '' "s/\${name}/$SVC/g" "$base"/BUILD 2>/dev/null || sed -i "s/\${name}/$SVC/g" "$base"/BUILD

cat > "$base"/app/api/main.py << 'EOF'
from fastapi import FastAPI


app = FastAPI(title="svc", version="0.1.0")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


def run() -> None:
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF

sed -i '' "s/title=\"svc\"/title=\"$SVC\"/" "$base"/app/api/main.py 2>/dev/null || true

cat > "$base"/app/worker/run.py << 'EOF'
def main() -> None:
    print("worker started")
EOF

cat > "$base"/infra/pulumi/Pulumi.yaml << 'EOF'
name: svc
runtime:
  name: python
EOF
sed -i '' "s/name: svc/name: $SVC/" "$base"/infra/pulumi/Pulumi.yaml 2>/dev/null || true

cat > "$base"/infra/pulumi/requirements.txt << 'EOF'
pulumi>=3.0.0
pulumi-aws>=6.0.0
EOF

cat > "$base"/infra/pulumi/__main__.py << 'EOF'
import os
from stack.infra.components.http_service import EcsHttpService
import pulumi

MODULE = os.getenv("MODULE", "svc")
AWS_REGION = os.getenv("AWS_REGION", "eu-west-2")
AWS_ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID", "")
PROJECT_SLUG = os.getenv("PROJECT_SLUG", "mono-template")
BRANCH = os.getenv("GITHUB_REF_NAME", "dev")
SHORT_SHA = (os.getenv("GITHUB_SHA", "") or "dev")[:7]
ECR_REPO = os.getenv("ECR_REPOSITORY", PROJECT_SLUG)
ECR_BASE = f"{AWS_ACCOUNT_ID}.dkr.ecr.{AWS_REGION}.amazonaws.com/{ECR_REPO}"

api_image = f"{ECR_BASE}:{MODULE}-{BRANCH}-{SHORT_SHA}"

svc = EcsHttpService(name=f"{MODULE}-api", image=api_image, port=8000, env={"SERVICE_NAME": MODULE})
pulumi.export("alb_dns", svc.alb_dns)
pulumi.export("url", svc.url)
EOF

echo "Service '$SVC' scaffolded. Update BUILD resolves as needed."
