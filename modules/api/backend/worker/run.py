import json
import os
import time
from platform.libs.shared.logging import get_logger
import boto3


log = get_logger("api.worker")
AWS_REGION = os.getenv("AWS_REGION", "eu-west-2")
QUEUE_URL = os.getenv("QUEUE_URL", "")
STATUS_BUCKET = os.getenv("STATUS_BUCKET", "")

sqs = boto3.client("sqs", region_name=AWS_REGION)
s3 = boto3.client("s3", region_name=AWS_REGION)


def process_message(msg: dict) -> None:
    attrs = msg.get("MessageAttributes") or {}
    cid = attrs.get("correlation_id", {}).get("StringValue")
    payload = attrs.get("payload", {}).get("StringValue")
    log.info("processing", extra={"correlation_id": cid})
    time.sleep(30)
    result = {"id": cid, "status": "done", "payload": payload}
    key = f"results/{cid}.json"
    s3.put_object(Bucket=STATUS_BUCKET, Key=key, Body=json.dumps(result).encode("utf-8"))
    log.info("completed", extra={"correlation_id": cid})


def main() -> None:
    if not QUEUE_URL or not STATUS_BUCKET:
        raise SystemExit("QUEUE_URL and STATUS_BUCKET must be set")
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

