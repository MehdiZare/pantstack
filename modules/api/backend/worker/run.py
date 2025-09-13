import json
import os
import time
from platform.libs.shared.aws import client as aws_client
from platform.libs.shared.aws import ensure_bucket, ensure_queue
from platform.libs.shared.logging import get_logger

log = get_logger("api.worker")
QUEUE_URL = os.getenv("QUEUE_URL", "")
STATUS_BUCKET = os.getenv("STATUS_BUCKET", "")
QUEUE_NAME = os.getenv("QUEUE_NAME", "api-queue")
BUCKET_NAME = os.getenv("BUCKET_NAME", "api-status")
LOCALSTACK = os.getenv("LOCALSTACK", "").lower() in ("1", "true", "yes", "on")

sqs = aws_client("sqs")
s3 = aws_client("s3")

if LOCALSTACK:
    if not QUEUE_URL:
        QUEUE_URL = ensure_queue(sqs, queue_name=QUEUE_NAME)
    if not STATUS_BUCKET:
        STATUS_BUCKET = BUCKET_NAME
        ensure_bucket(s3, bucket_name=STATUS_BUCKET)


def process_message(msg: dict) -> None:
    attrs = msg.get("MessageAttributes") or {}
    cid = attrs.get("correlation_id", {}).get("StringValue")
    payload = attrs.get("payload", {}).get("StringValue")
    log.info("processing", extra={"correlation_id": cid})
    time.sleep(30)
    result = {"id": cid, "status": "done", "payload": payload}
    key = f"results/{cid}.json"
    s3.put_object(
        Bucket=STATUS_BUCKET, Key=key, Body=json.dumps(result).encode("utf-8")
    )
    log.info("completed", extra={"correlation_id": cid})


def main() -> None:
    if not QUEUE_URL or not STATUS_BUCKET:
        raise SystemExit(
            "QUEUE_URL and STATUS_BUCKET must be set (or run with LOCALSTACK=true)"
        )
    while True:
        resp = sqs.receive_message(
            QueueUrl=QUEUE_URL,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=20,
            MessageAttributeNames=["All"],
        )
        for m in resp.get("Messages", []):
            try:
                process_message(m)
            finally:
                sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=m["ReceiptHandle"])


if __name__ == "__main__":
    main()
