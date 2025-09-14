import os

import pulumi
from stack.infra.components.http_service import EcsHttpService

PROJECT_SLUG = os.getenv("PROJECT_SLUG", "mono-template")
AWS_REGION = os.getenv("AWS_REGION", "eu-west-2")
AWS_ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID", "")
MODULE = os.getenv("MODULE", "web")

BRANCH = os.getenv("GITHUB_REF_NAME", "dev")
SHORT_SHA = (os.getenv("GITHUB_SHA", "") or "dev")[:7]
ECR_REPO = os.getenv("ECR_REPOSITORY", PROJECT_SLUG)
ECR_BASE = f"{AWS_ACCOUNT_ID}.dkr.ecr.{AWS_REGION}.amazonaws.com/{ECR_REPO}"

api_image = f"{ECR_BASE}:{MODULE}-{BRANCH}-{SHORT_SHA}"
EVENT_BUS_NAME = os.getenv("EVENT_BUS_NAME")
EVENT_BUS_STACK = os.getenv("EVENT_BUS_STACK")
if not EVENT_BUS_NAME and EVENT_BUS_STACK:
    try:
        ref = pulumi.StackReference(EVENT_BUS_STACK)
        EVENT_BUS_NAME = ref.get_output("bus_name")
    except Exception:
        EVENT_BUS_NAME = None

svc = EcsHttpService(
    name=f"{MODULE}-api",
    image=api_image,
    port=8000,
    env={
        "SERVICE_NAME": MODULE,
        **({"EVENT_BUS_NAME": EVENT_BUS_NAME} if EVENT_BUS_NAME else {}),
    },
)

pulumi.export("alb_dns", svc.alb_dns)
pulumi.export("url", svc.url)
