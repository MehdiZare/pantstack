import os

import pulumi
import pulumi_aws as aws

from stack.infra.components.http_service import EcsHttpService

PROJECT_SLUG = os.getenv("PROJECT_SLUG", "mono-template")
AWS_REGION = os.getenv("AWS_REGION", "eu-west-2")
AWS_ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID", "")
MODULE = os.getenv("MODULE", "auth")

BRANCH = os.getenv("GITHUB_REF_NAME", "dev")
SHORT_SHA = (os.getenv("GITHUB_SHA", "") or "dev")[:7]
ECR_REPO = os.getenv("ECR_REPOSITORY", PROJECT_SLUG)
ECR_BASE = f"{AWS_ACCOUNT_ID}.dkr.ecr.{AWS_REGION}.amazonaws.com/{ECR_REPO}"

api_image = f"{ECR_BASE}:{MODULE}-{BRANCH}-{SHORT_SHA}"

# DynamoDB users table
tbl = aws.dynamodb.Table(
    f"{MODULE}-users",
    attributes=[aws.dynamodb.TableAttributeArgs(name="pk", type="S")],
    hash_key="pk",
    billing_mode="PAY_PER_REQUEST",
)

policy = tbl.arn.apply(
    lambda arn: pulumi.Output.secret(
        '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":["dynamodb:GetItem","dynamodb:PutItem"],"Resource":"'
        + arn
        + '"}]}'
    )
)

svc = EcsHttpService(
    name=f"{MODULE}-api",
    image=api_image,
    port=8000,
    env={
        "SERVICE_NAME": MODULE,
        "AUTH_USERS_TABLE": tbl.name,
    },
    task_inline_policy_json=policy,
)

pulumi.export("alb_dns", svc.alb_dns)
pulumi.export("url", svc.url)
pulumi.export("users_table", tbl.name)
