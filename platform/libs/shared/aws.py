import os
from typing import Optional

import boto3


def _use_localstack() -> bool:
    val = os.getenv("LOCALSTACK", "").lower()
    return val in ("1", "true", "yes", "on")


def client(service_name: str, *, region: Optional[str] = None):
    region_name = region or os.getenv(
        "AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "eu-west-2")
    )
    if _use_localstack() or os.getenv("AWS_ENDPOINT_URL"):
        endpoint = os.getenv("AWS_ENDPOINT_URL", "http://localhost:4566")
        return boto3.client(
            service_name, region_name=region_name, endpoint_url=endpoint
        )
    return boto3.client(service_name, region_name=region_name)


def ensure_queue(sqs_client, *, queue_name: str) -> str:
    resp = sqs_client.create_queue(QueueName=queue_name)
    return resp["QueueUrl"]


def ensure_bucket(s3_client, *, bucket_name: str) -> None:
    region_name = s3_client.meta.region_name
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        return
    except Exception:
        pass
    if region_name == "us-east-1":
        s3_client.create_bucket(Bucket=bucket_name)
    else:
        s3_client.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={"LocationConstraint": region_name},
        )
