import os

import pytest

from services.web.adapters.repositories.s3_jobs import S3JobRepository
from services.web.adapters.repositories.sqs_queue import SqsQueue


def _is_localstack_enabled() -> bool:
    return os.getenv("LOCALSTACK", "").lower() in ("1", "true", "yes", "on")


@pytest.mark.integration
def test_sqs_and_s3_round_trip(monkeypatch):
    if not _is_localstack_enabled():
        pytest.skip("LocalStack not enabled")

    # Use isolated names to avoid clashing with developer runs
    monkeypatch.setenv("QUEUE_NAME", "web-queue-int")
    monkeypatch.setenv("BUCKET_NAME", "web-status-int")

    q = SqsQueue.from_env()
    repo = S3JobRepository.from_env()

    cid = q.publish("content.generate", {"title": "t", "topic": "x"})

    # Simulate worker lifecycle using the repository against LocalStack S3
    repo.mark_running(cid)
    repo.mark_completed(cid, {"ok": True})

    st = repo.get_status(cid)
    assert st is not None
    assert st["status"] == "completed"
