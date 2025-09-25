from services.web.domain.services.jobs import cancel_job, get_job_status, schedule_job


class FakeQueue:
    def __init__(self):
        self.published: list[tuple[str, dict]] = []

    def publish(self, job_type: str, params: dict) -> str:
        self.published.append((job_type, params))
        return "cid-123"


class FakeRepo:
    def __init__(self):
        self.canceled: list[str] = []
        self.status: dict[str, dict] = {}

    def get_status(self, cid: str):
        return self.status.get(cid)

    def mark_canceled(self, cid: str) -> None:
        self.canceled.append(cid)


def test_schedule_job_publishes_and_returns_id():
    q = FakeQueue()
    out = schedule_job(
        q, type("Req", (), {"job_type": "content.generate", "params": {"a": 1}})()
    )
    assert out == {"id": "cid-123"}
    assert q.published == [("content.generate", {"a": 1})]


def test_get_and_cancel_job():
    r = FakeRepo()
    r.status["cid-1"] = {"status": "running"}
    assert get_job_status(r, "cid-1") == {"status": "running"}
    cancel_job(r, "cid-1")
    assert r.canceled == ["cid-1"]
