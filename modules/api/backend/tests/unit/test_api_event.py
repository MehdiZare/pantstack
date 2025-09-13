from modules.api.backend.worker.run import process_message


def test_process_message(monkeypatch):
    class S3Mock:
        def put_object(self, Bucket, Key, Body):  # noqa: N803
            assert Bucket and Key and Body

    import modules.api.backend.worker.run as worker

    worker.s3 = S3Mock()  # type: ignore
    worker.STATUS_BUCKET = "test-bucket"

    msg = {
        "MessageAttributes": {
            "correlation_id": {"StringValue": "abc", "DataType": "String"},
            "payload": {"StringValue": "{}", "DataType": "String"},
        }
    }

    # speed up test: patch sleep
    monkeypatch.setattr(worker.time, "sleep", lambda x: None)
    process_message(msg)
