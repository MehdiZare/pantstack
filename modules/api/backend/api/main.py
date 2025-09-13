import os
import uuid
from platform.libs.shared.aws import client as aws_client
from platform.libs.shared.aws import ensure_bucket, ensure_queue
from platform.libs.shared.logging import get_logger

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

log = get_logger("api")
app = FastAPI(title="api", version="0.1.0")

QUEUE_URL = os.getenv("QUEUE_URL", "")
STATUS_BUCKET = os.getenv("STATUS_BUCKET", "")
QUEUE_NAME = os.getenv("QUEUE_NAME", "api-queue")
BUCKET_NAME = os.getenv("BUCKET_NAME", "api-status")
LOCALSTACK = os.getenv("LOCALSTACK", "").lower() in ("1", "true", "yes", "on")

sqs = aws_client("sqs")
s3 = aws_client("s3")

if LOCALSTACK:
    # Bootstrap local resources if env vars are missing
    if not QUEUE_URL:
        QUEUE_URL = ensure_queue(sqs, queue_name=QUEUE_NAME)
    if not STATUS_BUCKET:
        STATUS_BUCKET = BUCKET_NAME
        ensure_bucket(s3, bucket_name=STATUS_BUCKET)


class TestEvent(BaseModel):
    payload: dict


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/test-event")
def submit_test_event(evt: TestEvent) -> dict[str, str]:
    if not QUEUE_URL:
        raise HTTPException(500, "QUEUE_URL not configured")
    correlation_id = str(uuid.uuid4())
    sqs.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody="test-event",
        MessageAttributes={
            "correlation_id": {"StringValue": correlation_id, "DataType": "String"},
            "payload": {"StringValue": str(evt.payload), "DataType": "String"},
        },
    )
    log.info("queued test-event", extra={"correlation_id": correlation_id})
    return {"id": correlation_id}


@app.get("/test-event/{correlation_id}")
def get_test_event_status(correlation_id: str) -> dict:
    if not STATUS_BUCKET:
        raise HTTPException(500, "STATUS_BUCKET not configured")
    key = f"results/{correlation_id}.json"
    try:
        obj = s3.get_object(Bucket=STATUS_BUCKET, Key=key)
        import json

        body = obj["Body"].read().decode("utf-8")
        return json.loads(body)
    except s3.exceptions.NoSuchKey:  # type: ignore[attr-defined]
        raise HTTPException(404, "pending")
    except Exception as e:  # noqa: BLE001
        log.info("status check error", extra={"error": str(e)})
        raise HTTPException(404, "pending")


def run() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
