import json
import os
import time
from platform.libs.shared.aws import client as aws_client
from platform.libs.shared.aws import ensure_queue
from platform.libs.shared.logging import get_logger

log = get_logger("admin.scheduler")

QUEUE_URL = os.getenv("QUEUE_URL", "")
QUEUE_NAME = os.getenv("QUEUE_NAME", "admin-queue")
LOCALSTACK = os.getenv("LOCALSTACK", "").lower() in ("1", "true", "yes", "on")

sqs = aws_client("sqs")

if LOCALSTACK and not QUEUE_URL:
    QUEUE_URL = ensure_queue(sqs, queue_name=QUEUE_NAME)


def main() -> None:
    if not QUEUE_URL:
        raise SystemExit("QUEUE_URL must be set (or run with LOCALSTACK=true)")
    log.info("scheduler starting", extra={"queue": QUEUE_URL})
    interval = int(os.getenv("SCHEDULE_INTERVAL", "60"))
    job_type = os.getenv("JOB_TYPE", "admin.dummy")
    payload = {"hello": "world"}
    while True:
        sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=job_type,
            MessageAttributes={
                "correlation_id": {
                    "StringValue": os.urandom(6).hex(),
                    "DataType": "String",
                },
                "params": {"StringValue": json.dumps(payload), "DataType": "String"},
            },
        )
        log.info("scheduled job", extra={"job_type": job_type})
        time.sleep(interval)


if __name__ == "__main__":
    main()
