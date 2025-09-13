import os
import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import boto3
from platform.libs.shared.logging import get_logger


log = get_logger("api")
app = FastAPI(title="api", version="0.1.0")

QUEUE_URL = os.getenv("QUEUE_URL", "")
STATUS_BUCKET = os.getenv("STATUS_BUCKET", "")
AWS_REGION = os.getenv("AWS_REGION", "eu-west-2")

sqs = boto3.client("sqs", region_name=AWS_REGION)
s3 = boto3.client("s3", region_name=AWS_REGION)


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

