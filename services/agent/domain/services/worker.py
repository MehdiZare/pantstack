import json
import time

from services.agent.domain.ports import JobRepository
from stack.agents.runner import run_agent


def process_message(repo: JobRepository, msg: dict) -> None:
    attrs = msg.get("MessageAttributes") or {}
    cid = attrs.get("correlation_id", {}).get("StringValue")
    params_raw = attrs.get("params", {}).get("StringValue")
    job_type = msg.get("Body") or "content.generate"
    try:
        params = json.loads(params_raw or "{}")
    except Exception:
        params = {}

    repo.mark_running(cid)

    for _ in range(5):
        if repo.is_canceled(cid):
            repo.mark_failed(cid, "canceled")
            return
        time.sleep(1)

    result = run_agent(job_type, params)
    repo.mark_completed(cid, result)
