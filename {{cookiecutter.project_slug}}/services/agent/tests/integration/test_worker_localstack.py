import json
import os

import pytest

from services.agent.adapters.repositories.s3_jobs import S3JobRepository
from services.agent.domain.services.worker import process_message


def _is_localstack_enabled() -> bool:
    return os.getenv("LOCALSTACK", "").lower() in ("1", "true", "yes", "on")


@pytest.mark.integration
def test_worker_process_marks_status_in_s3(monkeypatch):
    if not _is_localstack_enabled():
        pytest.skip("LocalStack not enabled")

    # Speed up worker
    monkeypatch.setattr("time.sleep", lambda *_: None)

    # Ensure the bucket exists and use a test bucket
    monkeypatch.setenv("BUCKET_NAME", "agent-status-int")
    repo = S3JobRepository.from_env()

    # Avoid any external agent calls
    import services.agent.domain.services.worker as mod

    monkeypatch.setattr(mod, "run_agent", lambda *_args, **_kw: {"ok": True})

    correlation_id = "abc-int"
    msg = {
        "Body": "content.generate",
        "MessageAttributes": {
            "correlation_id": {"StringValue": correlation_id, "DataType": "String"},
            "params": {"StringValue": json.dumps({}), "DataType": "String"},
        },
    }

    process_message(repo, msg)

    # Read back status JSON directly from S3
    obj = repo.s3.get_object(Bucket=repo.bucket, Key=repo._key(correlation_id))
    body = obj["Body"].read().decode("utf-8")
    data = json.loads(body)
    assert data.get("status") == "completed"
