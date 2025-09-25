import json
import os
import uuid

from stack.libs.shared.aws import client as aws_client
from stack.libs.shared.aws import ensure_queue


class SqsQueue:
    def __init__(self, queue_url: str):
        self.queue_url = queue_url
        self.sqs = aws_client("sqs")

    @classmethod
    def from_env(cls) -> "SqsQueue":
        qurl = os.getenv("QUEUE_URL")
        if not qurl and os.getenv("LOCALSTACK", "").lower() in (
            "1",
            "true",
            "yes",
            "on",
        ):
            name = os.getenv("QUEUE_NAME", "web-queue")
            qurl = ensure_queue(aws_client("sqs"), queue_name=name)
        if not qurl:
            raise RuntimeError("QUEUE_URL not configured")
        return cls(queue_url=qurl)

    def publish(self, job_type: str, params: dict) -> str:
        cid = str(uuid.uuid4())
        self.sqs.send_message(
            QueueUrl=self.queue_url,
            MessageBody=job_type,
            MessageAttributes={
                "correlation_id": {"StringValue": cid, "DataType": "String"},
                "params": {
                    "StringValue": json.dumps(params, default=str),
                    "DataType": "String",
                },
            },
        )
        return cid
