import os
from platform.agents.runner import run_agent

from celery import Celery

broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
result_backend = os.getenv("CELERY_RESULT_BACKEND", broker_url)

app = Celery("admin", broker=broker_url, backend=result_backend)


@app.task(name="admin.run_agent")
def run_agent_task(job_type: str, params: dict) -> dict:
    return run_agent(job_type, params)
