import os
import uuid
from platform.libs.shared.aws import client as aws_client
from platform.libs.shared.aws import ensure_bucket, ensure_queue
from platform.libs.shared.logging import get_logger

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel

log = get_logger("admin.api")
app = FastAPI(title="admin", version="0.1.0")

QUEUE_URL = os.getenv("QUEUE_URL", "")
STATUS_BUCKET = os.getenv("STATUS_BUCKET", "")
QUEUE_NAME = os.getenv("QUEUE_NAME", "admin-queue")
BUCKET_NAME = os.getenv("BUCKET_NAME", "admin-status")
LOCALSTACK = os.getenv("LOCALSTACK", "").lower() in ("1", "true", "yes", "on")

sqs = aws_client("sqs")
s3 = aws_client("s3")

if LOCALSTACK:
    if not QUEUE_URL:
        QUEUE_URL = ensure_queue(sqs, queue_name=QUEUE_NAME)
    if not STATUS_BUCKET:
        STATUS_BUCKET = BUCKET_NAME
        ensure_bucket(s3, bucket_name=STATUS_BUCKET)


class ScheduleRequest(BaseModel):
    job_type: str
    params: dict


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return '<meta http-equiv="refresh" content="0; url=/admin" />'


@app.get("/admin", response_class=HTMLResponse)
def admin_home() -> str:
    return """
    <html><head><title>Admin</title>
    <style>body{{font-family:sans-serif;max-width:720px;margin:2rem auto}}label{{display:block;margin:.5rem 0}}</style>
    </head><body>
      <h1>Schedule Job</h1>
      <form method=post action="/admin/jobs">
        <label>Job Type <input name=job_type value="content.generate" /></label>
        <label>Title <input name=title placeholder="Post title" /></label>
        <label>Topic <input name=topic placeholder="Topic" /></label>
        <button type=submit>Schedule</button>
      </form>
    </body></html>
    """


@app.post("/admin/jobs")
def schedule_job_form(
    job_type: str = Form(...), title: str = Form(""), topic: str = Form("")
) -> RedirectResponse:
    payload = {"title": title, "topic": topic}
    job = schedule_job(ScheduleRequest(job_type=job_type, params=payload))
    return RedirectResponse(url=f"/admin/jobs/{job['id']}/view", status_code=303)


@app.post("/admin/schedule")
def schedule_job(req: ScheduleRequest) -> dict[str, str]:
    # Default to sqs for simplicity; celery remains optional
    backend = os.getenv("QUEUE_BACKEND", "celery").lower()
    if backend == "celery":
        from modules.admin.backend.worker.celery_app import run_agent_task

        async_result = run_agent_task.delay(req.job_type, req.params)
        log.info("scheduled celery job", extra={"task_id": async_result.id})
        return {"id": async_result.id}
    else:
        if not QUEUE_URL:
            raise HTTPException(500, "QUEUE_URL not configured")
        correlation_id = str(uuid.uuid4())
        sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=req.job_type,
            MessageAttributes={
                "correlation_id": {"StringValue": correlation_id, "DataType": "String"},
                "params": {"StringValue": json_dumps(req.params), "DataType": "String"},
            },
        )
        log.info(
            "scheduled job",
            extra={"correlation_id": correlation_id, "job_type": req.job_type},
        )
        return {"id": correlation_id}


@app.get("/admin/jobs/{correlation_id}")
def get_job_status(correlation_id: str) -> dict:
    backend = os.getenv("QUEUE_BACKEND", "celery").lower()
    if backend == "celery":
        from celery.result import AsyncResult

        from modules.admin.backend.worker.celery_app import app as celery_app

        res = AsyncResult(correlation_id, app=celery_app)
        if res.ready():
            try:
                return {"id": correlation_id, "status": "completed", "result": res.get()}  # type: ignore[return-value]
            except Exception as e:  # noqa: BLE001
                return {"id": correlation_id, "status": "failed", "error": str(e)}
        return {"id": correlation_id, "status": res.status.lower()}
    else:
        if not STATUS_BUCKET:
            raise HTTPException(500, "STATUS_BUCKET not configured")
        key = f"results/{correlation_id}.json"
        try:
            obj = s3.get_object(Bucket=STATUS_BUCKET, Key=key)
            import json

            body = obj["Body"].read().decode("utf-8")
            return json.loads(body)
        except s3.exceptions.NoSuchKey:  # type: ignore[attr-defined]
            return {"id": correlation_id, "status": "pending"}
        except Exception as e:  # noqa: BLE001
            log.info("status check error", extra={"error": str(e)})
            return {"id": correlation_id, "status": "pending"}


@app.get("/admin/jobs/{correlation_id}/view", response_class=HTMLResponse)
def view_job(correlation_id: str) -> str:
    j = get_job_status(correlation_id)
    status = j.get("status", "pending")
    return f"""
    <html><head><title>Job {correlation_id}</title>
    <style>body{{font-family:sans-serif;max-width:720px;margin:2rem auto}}</style>
    </head><body>
      <h1>Job {correlation_id}</h1>
      <p>Status: <b>{status}</b></p>
      <form method=post action="/admin/jobs/{correlation_id}/cancel" style="display:inline"><button {'disabled' if status in ['completed', 'failed', 'canceled'] else ''}>Cancel</button></form>
      <form method=get action="/admin/jobs/{correlation_id}/view" style="display:inline;margin-left:1rem"><button>Refresh</button></form>
      <pre>{html_escape(json_dumps(j))}</pre>
      <p><a href="/admin">Back</a></p>
    </body></html>
    """


@app.post("/admin/jobs/{correlation_id}/cancel")
def cancel_job(correlation_id: str) -> RedirectResponse:
    if not STATUS_BUCKET:
        raise HTTPException(500, "STATUS_BUCKET not configured")
    s3.put_object(Bucket=STATUS_BUCKET, Key=f"cancels/{correlation_id}", Body=b"1")
    return RedirectResponse(url=f"/admin/jobs/{correlation_id}/view", status_code=303)


def json_dumps(obj: dict) -> str:
    import json

    return json.dumps(obj, default=str)


def run() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)


def html_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )
