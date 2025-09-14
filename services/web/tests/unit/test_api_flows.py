from services.web.app.api.main import cancel, job_status, schedule_job_form


class FakeQueue:
    def __init__(self, cid: str = "abc"):
        self.cid = cid
        self.published = []

    def publish(self, job_type: str, params: dict) -> str:
        self.published.append((job_type, params))
        return self.cid


class FakeRepo:
    def __init__(self, status: dict | None = None):
        self.status_by_id = status or {}
        self.canceled = []

    def get_status(self, cid: str):
        return self.status_by_id.get(cid)

    def mark_canceled(self, cid: str):
        self.canceled.append(cid)


def test_schedule_and_status_routes(monkeypatch):
    q = FakeQueue("job-1")
    r = FakeRepo({"job-1": {"status": "running"}})

    import services.web.app.api.main as mod

    monkeypatch.setattr(mod, "_provide_queue", lambda: q)
    monkeypatch.setattr(mod, "_provide_repo", lambda: r)

    # Call the route function directly (unit-level)
    resp = schedule_job_form("content.generate", "t", "x")
    assert getattr(resp, "status_code", 0) == 303
    assert resp.headers["location"] == "/admin/jobs/job-1/view"

    # Status returns the status dict via function
    st = job_status("job-1")
    assert st == {"status": "running"}


def test_cancel_route(monkeypatch):
    q = FakeQueue("job-2")
    r = FakeRepo({"job-2": {"status": "running"}})

    import services.web.app.api.main as mod

    monkeypatch.setattr(mod, "_provide_queue", lambda: q)
    monkeypatch.setattr(mod, "_provide_repo", lambda: r)

    resp = cancel("job-2")
    assert getattr(resp, "status_code", 0) == 303
    assert "job-2" in r.canceled
