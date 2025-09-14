import json
import time
from typing import Any, Mapping


def run_agent(job_type: str, params: Mapping[str, Any]) -> dict[str, Any]:
    """Run a placeholder long-running agent.

    If LangGraph is available, this is where you'd build a graph and execute it.
    For the template, we simulate work so the flow is demonstrable offline.
    """
    # Simulate work
    time.sleep(2)
    # Echo-style result
    return {
        "job_type": job_type,
        "status": "completed",
        "summary": f"Processed with params: {json.dumps(params, default=str)}",
    }
