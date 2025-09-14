from services.agent.domain.services.worker import process_message


class FakeRepo:
    def __init__(self):
        self.marks = []

    def mark_running(self, cid):
        self.marks.append(("running", cid))

    def is_canceled(self, cid):
        return False

    def mark_completed(self, cid, result):
        self.marks.append(("completed", cid))

    def mark_failed(self, cid, error):
        self.marks.append(("failed", cid))


def test_process_message(monkeypatch):
    # Patch run_agent to avoid sleep
    import services.agent.domain.services.worker as mod

    monkeypatch.setattr(mod, "run_agent", lambda job_type, params: {"ok": True})

    repo = FakeRepo()
    msg = {
        "Body": "content.generate",
        "MessageAttributes": {
            "correlation_id": {"StringValue": "abc", "DataType": "String"},
            "params": {"StringValue": "{}", "DataType": "String"},
        },
    }
    process_message(repo, msg)
    assert ("completed", "abc") in repo.marks
