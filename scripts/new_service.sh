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

# Create directory structure
mkdir -p "$base"/app/api "$base"/app/worker
mkdir -p "$base"/domain/models "$base"/domain/services "$base"/domain/ports
mkdir -p "$base"/adapters/repositories
mkdir -p "$base"/public
mkdir -p "$base"/infrastructure
mkdir -p "$base"/tests/unit "$base"/tests/integration

# Create __init__.py files
touch "$base"/__init__.py
touch "$base"/app/__init__.py
touch "$base"/app/api/__init__.py
touch "$base"/app/worker/__init__.py
touch "$base"/domain/__init__.py
touch "$base"/domain/models/__init__.py
touch "$base"/domain/services/__init__.py
touch "$base"/domain/ports/__init__.py
touch "$base"/adapters/__init__.py
touch "$base"/adapters/repositories/__init__.py
touch "$base"/public/__init__.py
touch "$base"/tests/__init__.py
touch "$base"/tests/unit/__init__.py
touch "$base"/tests/integration/__init__.py

cat > "$base"/BUILD << 'EOF'
python_sources(
    name="${name}_core",
    sources=["domain/**/*.py", "adapters/**/*.py", "public/**/*.py"],
    resolve="${name}_core",
    dependencies=[
        "stack/libs/shared",
        "stack/events/libs",
        "3rdparty/python:${name}_core_reqs",
    ],
    overrides={
        "domain/**/*.py": {
            "dependencies": [
                "3rdparty/python:${name}_core_reqs#pydantic",
            ]
        },
    },
)

python_sources(
    name="${name}_api_src",
    sources=["app/api/**/*.py"],
    resolve="${name}_api",
    dependencies=[":${name}_core", "3rdparty/python:${name}_api_reqs"],
    overrides={
        "app/api/**/*.py": {
            "dependencies": [
                "3rdparty/python:${name}_api_reqs#fastapi",
                "3rdparty/python:${name}_api_reqs#uvicorn",
                "3rdparty/python:${name}_api_reqs#pydantic",
            ]
        },
    },
)

python_sources(
    name="${name}_worker_src",
    sources=["app/worker/**/*.py"],
    resolve="${name}_core",
    dependencies=[":${name}_core"],
)

pex_binary(
    name="${name}_api_pex",
    entry_point="services.${name}.app.api.main:run",
    resolve="${name}_api",
    dependencies=[":${name}_api_src"],
)

pex_binary(
    name="${name}_worker_pex",
    entry_point="services.${name}.app.worker.run:main",
    resolve="${name}_core",
    dependencies=[":${name}_worker_src"],
)

docker_image(
    name="${name}_image",
    dependencies=[":${name}_api_pex"],
    image_tags=["latest"],
    source="Dockerfile.api",
)

docker_image(
    name="${name}_worker_image",
    dependencies=[":${name}_worker_pex"],
    image_tags=["latest"],
    source="Dockerfile.worker",
)

python_tests(
    name="unit",
    sources=["tests/unit/**/*.py"],
    resolve="${name}_api",
    dependencies=[
        ":${name}_core",
        ":${name}_api_src",
        ":${name}_worker_src",
        "3rdparty/python:${name}_api_reqs#fastapi",
        "3rdparty/python:${name}_api_reqs#httpx",
    ],
)

python_tests(
    name="integration",
    sources=["tests/integration/**/*.py"],
    resolve="${name}_api",
    dependencies=[":${name}_core"],
)
EOF

sed -i '' "s/\${name}/$SVC/g" "$base"/BUILD 2>/dev/null || sed -i "s/\${name}/$SVC/g" "$base"/BUILD

cat > "$base"/app/api/main.py << 'EOF'
from fastapi import FastAPI


app = FastAPI(title="${name}", version="0.1.0")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "${name}", "status": "running"}


def run() -> None:
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    run()
EOF

cat > "$base"/app/worker/run.py << 'EOF'
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    """Main entry point for the worker."""
    logger.info("Worker started for service: ${name}")
    # TODO: Add worker logic here


if __name__ == "__main__":
    main()
EOF

# Create Dockerfiles
cat > "$base"/Dockerfile.api << 'EOF'
FROM python:3.11-slim

WORKDIR /app

COPY . .

ENTRYPOINT ["python", "-m", "services.${name}.app.api.main"]
EOF

cat > "$base"/Dockerfile.worker << 'EOF'
FROM python:3.11-slim

WORKDIR /app

COPY . .

ENTRYPOINT ["python", "-m", "services.${name}.app.worker.run"]
EOF

# Create Pulumi infrastructure
cat > "$base"/infrastructure/Pulumi.yaml << 'EOF'
name: ${name}
runtime:
  name: python
  options:
    virtualenv: venv
backend:
  url: s3://pulumi-state-${name}
EOF

cat > "$base"/infrastructure/requirements.txt << 'EOF'
pulumi>=3.0.0
pulumi-aws>=6.0.0
EOF

cat > "$base"/infrastructure/__main__.py << 'EOF'
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

# Replace ${name} placeholders with actual service name
sed -i '' "s/\${name}/$SVC/g" "$base"/BUILD 2>/dev/null || sed -i "s/\${name}/$SVC/g" "$base"/BUILD
sed -i '' "s/\${name}/$SVC/g" "$base"/app/api/main.py 2>/dev/null || sed -i "s/\${name}/$SVC/g" "$base"/app/api/main.py
sed -i '' "s/\${name}/$SVC/g" "$base"/app/worker/run.py 2>/dev/null || sed -i "s/\${name}/$SVC/g" "$base"/app/worker/run.py
sed -i '' "s/\${name}/$SVC/g" "$base"/Dockerfile.api 2>/dev/null || sed -i "s/\${name}/$SVC/g" "$base"/Dockerfile.api
sed -i '' "s/\${name}/$SVC/g" "$base"/Dockerfile.worker 2>/dev/null || sed -i "s/\${name}/$SVC/g" "$base"/Dockerfile.worker
sed -i '' "s/\${name}/$SVC/g" "$base"/infrastructure/Pulumi.yaml 2>/dev/null || sed -i "s/\${name}/$SVC/g" "$base"/infrastructure/Pulumi.yaml
sed -i '' "s/\${name}/$SVC/g" "$base"/infrastructure/__main__.py 2>/dev/null || sed -i "s/\${name}/$SVC/g" "$base"/infrastructure/__main__.py

# Create requirements files
cat > "3rdparty/python/requirements-$SVC-core.txt" << 'EOF'
pydantic>=2.0.0
EOF

cat > "3rdparty/python/requirements-$SVC-api.txt" << 'EOF'
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
pydantic>=2.0.0
httpx>=0.24.0
python-multipart>=0.0.6
EOF

# Update pants.toml with new resolvers
if [ -f "scripts/update_pants_resolvers.sh" ]; then
  ./scripts/update_pants_resolvers.sh "$SVC"
else
  echo "\nNOTE: Remember to add the following to pants.toml under [python.resolves]:"
  echo "  ${SVC}_core = \"lockfiles/${SVC}_core.lock\""
  echo "  ${SVC}_api = \"lockfiles/${SVC}_api.lock\""
  echo ""
fi

echo ""
echo "Service '$SVC' scaffolded successfully."
echo "Next steps:"
echo "  1. Run: ./pants generate-lockfiles"
echo "  2. Run: ./pants test services/$SVC::"
