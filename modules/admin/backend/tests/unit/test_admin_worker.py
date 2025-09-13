import json


def test_process_message_completes(monkeypatch):
    import modules.admin.backend.worker.run as worker

    captured = {}

    class S3Mock:
        def put_object(self, Bucket, Key, Body):  # noqa: N803
            captured["Bucket"] = Bucket
            captured["Key"] = Key
            captured["Body"] = Body

        def head_object(self, Bucket, Key):  # noqa: N803
            raise Exception("not canceled")

    # Patch dependencies
    worker.s3 = S3Mock()  # type: ignore
    worker.STATUS_BUCKET = "test-bucket"
    worker.post_to_strapi = lambda *a, **k: {"ok": True}  # type: ignore
    monkeypatch.setattr(worker.time, "sleep", lambda x: None)

    msg = {
        "Body": "content.generate",
        "MessageAttributes": {
            "correlation_id": {"StringValue": "abc", "DataType": "String"},
            "params": {
                "StringValue": json.dumps({"title": "T", "topic": "X"}),
                "DataType": "String",
            },
        },
    }

    worker.process_message(msg)
    assert captured["Bucket"] == "test-bucket"
    assert captured["Key"].startswith("results/")
    out = json.loads(captured["Body"].decode("utf-8"))
    assert out["status"] == "completed"
