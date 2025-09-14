import os

import pulumi
import pulumi_aws as aws

from stack.infra.components.worker_service import EcsWorkerService

PROJECT_SLUG = os.getenv("PROJECT_SLUG", "mono-template")
AWS_REGION = os.getenv("AWS_REGION", "eu-west-2")
AWS_ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID", "")
MODULE = os.getenv("MODULE", "agent")

BRANCH = os.getenv("GITHUB_REF_NAME", "dev")
SHORT_SHA = (os.getenv("GITHUB_SHA", "") or "dev")[:7]
ECR_REPO = os.getenv("ECR_REPOSITORY", PROJECT_SLUG)
ECR_BASE = f"{AWS_ACCOUNT_ID}.dkr.ecr.{AWS_REGION}.amazonaws.com/{ECR_REPO}"

worker_image = f"{ECR_BASE}:{MODULE}-worker-{BRANCH}-{SHORT_SHA}"

# Status bucket (owned by agent)
bucket = aws.s3.BucketV2(f"{MODULE}-status", force_destroy=True)

# Agent requests queue
queue = aws.sqs.Queue(f"{MODULE}-requests", visibility_timeout_seconds=300)

# EventBridge bus reference (prefer env), fallback to local bus
bus_name = os.getenv("EVENT_BUS_NAME")
if bus_name:
    bus = aws.cloudwatch.get_event_bus(name=bus_name)
    bus_arn = bus.arn
else:
    local_bus = aws.cloudwatch.EventBus(f"{MODULE}-bus")
    bus_arn = local_bus.arn

# Allow EventBridge to send to this queue
aws.sqs.QueuePolicy(
    f"{MODULE}-queue-policy",
    queue_url=queue.url,
    policy=pulumi.Output.all(queue.arn, bus_arn).apply(
        lambda vals: pulumi.Output.secret(
            '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"events.amazonaws.com"},"Action":"sqs:SendMessage","Resource":"'
            + vals[0]
            + '","Condition":{"ArnEquals":{"aws:SourceArn":"'
            + vals[1]
            + '"}}}]}'
        )
    ),
)

# Route jobs.requested to the agent queue
rule = aws.cloudwatch.EventRule(
    f"{MODULE}-jobs-requested",
    event_bus_name=bus_name if bus_name else None,
    event_pattern='{"detail-type":["jobs.requested"]}',
)

aws.cloudwatch.EventTarget(
    f"{MODULE}-target-queue",
    rule=rule.name,
    event_bus_name=bus_name if bus_name else None,
    arn=queue.arn,
)

# Task IAM: allow reading from SQS queue and writing to S3 bucket
policy = pulumi.Output.all(queue.arn, bucket.arn).apply(
    lambda vals: pulumi.Output.secret(
        '{"Version":"2012-10-17","Statement":[\
            {"Effect":"Allow","Action":["sqs:ReceiveMessage","sqs:DeleteMessage","sqs:GetQueueAttributes"],"Resource":"'
        + vals[0]
        + '"},\
            {"Effect":"Allow","Action":["s3:PutObject","s3:GetObject","s3:HeadObject"],"Resource":"'
        + vals[1]
        + '/*"}\
        ]}'
    )
)

svc = EcsWorkerService(
    name=f"{MODULE}-worker",
    image=worker_image,
    env={
        "QUEUE_URL": queue.url,
        "STATUS_BUCKET": bucket.bucket,
        "SERVICE_NAME": MODULE,
    },
    task_inline_policy_json=policy,
)

pulumi.export("queue_url", queue.url)
pulumi.export("status_bucket", bucket.bucket)
