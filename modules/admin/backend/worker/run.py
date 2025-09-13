import json
import os
import time
from platform.agents.runner import run_agent
from platform.libs.shared.aws import client as aws_client
from platform.libs.shared.aws import ensure_bucket, ensure_queue
from platform.libs.shared.logging import get_logger

import requests

log = get_logger("admin.worker")

QUEUE_URL = os.getenv("QUEUE_URL", "")
STATUS_BUCKET = os.getenv("STATUS_BUCKET", "")
QUEUE_NAME = os.getenv("QUEUE_NAME", "admin-queue")
BUCKET_NAME = os.getenv("BUCKET_NAME", "admin-status")
LOCALSTACK = os.getenv("LOCALSTACK", "").lower() in ("1", "true", "yes", "on")

STRAPI_URL = os.getenv("STRAPI_URL")
STRAPI_TOKEN = os.getenv("STRAPI_TOKEN")

sqs = aws_client("sqs")
s3 = aws_client("s3")

if LOCALSTACK:
    if not QUEUE_URL:
        QUEUE_URL = ensure_queue(sqs, queue_name=QUEUE_NAME)
    if not STATUS_BUCKET:
        STATUS_BUCKET = BUCKET_NAME
        ensure_bucket(s3, bucket_name=STATUS_BUCKET)


def is_canceled(cid: str) -> bool:
    try:
        s3.head_object(Bucket=STATUS_BUCKET, Key=f"cancels/{cid}")
        return True
    except Exception:
        return False


def post_to_strapi(title: str, content: str) -> dict | None:
    if not STRAPI_URL or not STRAPI_TOKEN:
        return None
    try:
        resp = requests.post(
            f"{STRAPI_URL.rstrip('/')}/api/articles",
            json={"data": {"title": title, "content": content}},
            headers={"Authorization": f"Bearer {STRAPI_TOKEN}"},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:  # noqa: BLE001
        log.info("strapi error", extra={"error": str(e)})
        return None


def process_message(msg: dict) -> None:
    attrs = msg.get("MessageAttributes") or {}
    cid = attrs.get("correlation_id", {}).get("StringValue")
    params_raw = attrs.get("params", {}).get("StringValue")
    job_type = msg.get("Body") or "content.generate"
    try:
        params = json.loads(params_raw or "{}")
    except Exception:
        params = {}
    title = params.get("title") or "Untitled"
    topic = params.get("topic") or "general"

    # Mark running
    s3.put_object(
        Bucket=STATUS_BUCKET,
        Key=f"results/{cid}.json",
        Body=json.dumps({"id": cid, "status": "running"}).encode("utf-8"),
    )
    log.info("running agent", extra={"correlation_id": cid, "job_type": job_type})

    # Long-running work with cancel checks
    for _ in range(5):
        if is_canceled(cid):
            s3.put_object(
                Bucket=STATUS_BUCKET,
                Key=f"results/{cid}.json",
                Body=json.dumps({"id": cid, "status": "canceled"}).encode("utf-8"),
            )
            log.info("canceled", extra={"correlation_id": cid})
            return
        time.sleep(1)

    # Generate content (placeholder LangGraph call)
    result = run_agent(job_type, {"title": title, "topic": topic})
    content = f"Generated article on {topic}: {title}"
    strapi_resp = post_to_strapi(title, content)

    out = {
        "id": cid,
        "status": "completed",
        "result": result,
        "strapi": strapi_resp,
    }
    s3.put_object(
        Bucket=STATUS_BUCKET,
        Key=f"results/{cid}.json",
        Body=json.dumps(out).encode("utf-8"),
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
