import sys
import types

from modules.admin.backend.api.main import ScheduleRequest, get_job_status, schedule_job


def test_schedule_job_celery(monkeypatch):
    # Force celery backend
    monkeypatch.setenv("QUEUE_BACKEND", "celery")

    class FakeAsync:
        id = "task123"

    class FakeTask:
        def delay(self, job_type, params):  # noqa: D401
            assert job_type == "content.generate"
            assert params["title"] == "T"
            return FakeAsync()

    fake_mod = types.SimpleNamespace(run_agent_task=FakeTask())
    sys.modules["modules.admin.backend.worker.celery_app"] = fake_mod

    res = schedule_job(
        ScheduleRequest(job_type="content.generate", params={"title": "T"})
    )
    assert res["id"] == "task123"


def test_get_job_status_celery(monkeypatch):
    monkeypatch.setenv("QUEUE_BACKEND", "celery")

    class FakeRes:
        def __init__(self, *_args, **_kwargs):
            self._ready = True

        def ready(self):  # noqa: D401
            return True

        @property
        def status(self):  # noqa: D401
            return "SUCCESS"

        def get(self):  # noqa: D401
            return {"ok": True}

    # Patch celery.result.AsyncResult
    import celery.result as cr

    monkeypatch.setattr(cr, "AsyncResult", FakeRes, raising=False)

    out = get_job_status("task123")
    assert out["status"] in ("completed", "success")
