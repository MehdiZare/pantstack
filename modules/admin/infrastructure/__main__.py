import os
from platform.infra.components.http_service import EcsHttpService
from platform.infra.components.worker_service import EcsWorkerService

import pulumi

PROJECT_SLUG = os.getenv("PROJECT_SLUG", "mono-template")
AWS_REGION = os.getenv("AWS_REGION", "eu-west-2")
AWS_ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID", "")
MODULE = os.getenv("MODULE", "admin")

BRANCH = os.getenv("GITHUB_REF_NAME", "dev")
SHORT_SHA = (os.getenv("GITHUB_SHA", "") or "dev")[:7]
ECR_REPO = os.getenv("ECR_REPOSITORY", PROJECT_SLUG)
ECR_BASE = f"{AWS_ACCOUNT_ID}.dkr.ecr.{AWS_REGION}.amazonaws.com/{ECR_REPO}"

api_image = f"{ECR_BASE}:{MODULE}-{BRANCH}-{SHORT_SHA}"
celery_worker_image = f"{ECR_BASE}:{MODULE}-celery-worker-{BRANCH}-{SHORT_SHA}"

# API with sidecar Redis; expose port 8001
svc = EcsHttpService(
    name=f"{MODULE}-api",
    image=api_image,
    port=8001,
    env={
        "SERVICE_NAME": MODULE,
        "QUEUE_BACKEND": "celery",
        "CELERY_BROKER_URL": "redis://localhost:6379/0",
        "CELERY_RESULT_BACKEND": "redis://localhost:6379/0",
    },
    with_sidecar_redis=True,
    additional_containers=[
        {
            "name": f"{MODULE}-celery-worker",
            "image": celery_worker_image,
            "essential": True,
            "environment": [
                {"name": "SERVICE_NAME", "value": MODULE},
                {"name": "CELERY_BROKER_URL", "value": "redis://localhost:6379/0"},
                {"name": "CELERY_RESULT_BACKEND", "value": "redis://localhost:6379/0"},
            ],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": f"{PROJECT_SLUG}-{MODULE}-api-logs",
                    "awslogs-region": AWS_REGION,
                    "awslogs-stream-prefix": f"{MODULE}-celery",
                },
            },
        }
    ],
)

pulumi.export("alb_dns", svc.alb_dns)
pulumi.export("url", svc.url)
