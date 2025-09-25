from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

from services.web.domain.models.request import ScheduleRequest
from services.web.domain.services.jobs import cancel_job, get_job_status, schedule_job
from services.web.public.providers import provide_job_repo, provide_queue


def _provide_queue():
    return provide_queue()


def _provide_repo():
    return provide_job_repo()


app = FastAPI(title="web", version="0.1.0")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return '<meta http-equiv="refresh" content="0; url=/admin" />'


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/admin", response_class=HTMLResponse)
def admin_home() -> str:
    parts = [
        "<html><head><title>Admin</title>",
        "<style>",
        "body{font-family:sans-serif;max-width:720px;margin:2rem auto}",
        "label{display:block;margin:.5rem 0}",
        "</style>",
        "</head><body>",
        "  <h1>Schedule Job</h1>",
        '  <form method=post action="/admin/jobs">',
        '    <label>Job Type <input name=job_type value="content.generate" /></label>',
        '    <label>Title <input name=title placeholder="Post title" /></label>',
        '    <label>Topic <input name=topic placeholder="Topic" /></label>',
        "    <button type=submit>Schedule</button>",
        "  </form>",
        "</body></html>",
    ]
    return "\n".join(parts)


@app.post("/admin/jobs")
def schedule_job_form(
    job_type: str = Form(...), title: str = Form(""), topic: str = Form("")
) -> RedirectResponse:
    payload = {"title": title, "topic": topic}
    job = schedule_job(
        _provide_queue(), ScheduleRequest(job_type=job_type, params=payload)
    )
    return RedirectResponse(url=f"/admin/jobs/{job['id']}/view", status_code=303)


@app.post("/admin/schedule")
def schedule(req: ScheduleRequest) -> dict[str, str]:
    out = schedule_job(_provide_queue(), req)
    return out


@app.get("/admin/jobs/{correlation_id}")
def job_status(correlation_id: str) -> dict:
    repo = _provide_repo()
    st = get_job_status(repo, correlation_id)
    if st is None:
        raise HTTPException(404, "pending")
    return st


@app.get("/admin/jobs/{correlation_id}/view", response_class=HTMLResponse)
def view_job(correlation_id: str) -> str:
    j = job_status(correlation_id)
    status = j.get("status", "pending")
    disabled = "disabled" if status in ["completed", "failed", "canceled"] else ""
    parts = [
        f"<html><head><title>Job {correlation_id}</title>",
        "<style>",
        "body{font-family:sans-serif;max-width:720px;margin:2rem auto}",
        "</style>",
        "</head><body>",
        f"  <h1>Job {correlation_id}</h1>",
        f"  <p>Status: <b>{status}</b></p>",
        f'  <form method=post action="/admin/jobs/{correlation_id}/cancel" style="display:inline">',
        f"    <button {disabled}>Cancel</button>",
        "  </form>",
        f'  <form method=get action="/admin/jobs/{correlation_id}/view" style="display:inline;margin-left:1rem">',
        "    <button>Refresh</button>",
        "  </form>",
        f"  <pre>{_html_escape(_json_dumps(j))}</pre>",
        '  <p><a href="/admin">Back</a></p>',
        "</body></html>",
    ]
    return "\n".join(parts)


@app.post("/admin/jobs/{correlation_id}/cancel")
def cancel(correlation_id: str) -> RedirectResponse:
    cancel_job(_provide_repo(), correlation_id)
    return RedirectResponse(url=f"/admin/jobs/{correlation_id}/view", status_code=303)


def _json_dumps(obj: dict) -> str:
    import json

    return json.dumps(obj, default=str)


def _html_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


def run() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
