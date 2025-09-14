import os

from services.agent.domain.services.worker import process_message
from services.agent.public.providers import provide_job_repo
from stack.libs.shared.aws import client as aws_client
from stack.libs.shared.aws import ensure_bucket, ensure_queue


def main() -> None:
    sqs = aws_client("sqs")
    s3 = aws_client("s3")
    queue_url = os.getenv("QUEUE_URL")
    bucket = os.getenv("STATUS_BUCKET") or os.getenv("BUCKET_NAME") or "agent-status"
    if os.getenv("LOCALSTACK", "").lower() in ("1", "true", "yes", "on"):
        queue_url = queue_url or ensure_queue(
            sqs, queue_name=os.getenv("QUEUE_NAME", "agent-queue")
        )
        ensure_bucket(s3, bucket_name=bucket)
    if not queue_url:
        raise SystemExit("QUEUE_URL must be set")

    repo = provide_job_repo()
    while True:
        resp = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=20,
            MessageAttributeNames=["All"],
        )
        for m in resp.get("Messages", []):
            try:
                # If delivered from EventBridge, body is JSON with detail
                body = m.get("Body")
                if body and body.strip().startswith("{"):
                    import json

                    try:
                        payload = json.loads(body)
                        detail = payload.get("detail") or {}
                        # Normalize to legacy shape for process_message
                        m = {
                            "Body": detail.get("job_type"),
                            "MessageAttributes": {
                                "correlation_id": {
                                    "StringValue": detail.get("correlation_id", ""),
                                    "DataType": "String",
                                },
                                "params": {
                                    "StringValue": json.dumps(
                                        detail.get("params") or {}
                                    ),
                                    "DataType": "String",
                                },
                            },
                        }
                    except Exception:
                        pass
                process_message(repo, m)
            finally:
                sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=m["ReceiptHandle"])
