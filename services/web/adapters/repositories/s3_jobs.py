import json
import os

from stack.libs.shared.aws import client as aws_client
from stack.libs.shared.aws import ensure_bucket


class S3JobRepository:
    def __init__(self, bucket: str, prefix: str = "results/"):
        self.bucket = bucket
        self.prefix = prefix
        self.s3 = aws_client("s3")

    @classmethod
    def from_env(cls) -> "S3JobRepository":
        bucket = os.getenv("STATUS_BUCKET") or os.getenv("BUCKET_NAME") or "web-status"
        if os.getenv("LOCALSTACK", "").lower() in ("1", "true", "yes", "on"):
            ensure_bucket(aws_client("s3"), bucket_name=bucket)
        return cls(bucket=bucket)

    def _key(self, cid: str) -> str:
        return f"{self.prefix}{cid}.json"

    def get_status(self, correlation_id: str) -> dict | None:
        try:
            obj = self.s3.get_object(Bucket=self.bucket, Key=self._key(correlation_id))
            body = obj["Body"].read().decode("utf-8")
            return json.loads(body)
        except self.s3.exceptions.NoSuchKey:  # type: ignore[attr-defined]
            return None
        except Exception:
            return None

    def mark_running(self, correlation_id: str) -> None:
        self.s3.put_object(
            Bucket=self.bucket,
            Key=self._key(correlation_id),
            Body=json.dumps({"id": correlation_id, "status": "running"}).encode(
                "utf-8"
            ),
        )

    def mark_completed(self, correlation_id: str, result: dict) -> None:
        out = {"id": correlation_id, "status": "completed", "result": result}
        self.s3.put_object(
            Bucket=self.bucket,
            Key=self._key(correlation_id),
            Body=json.dumps(out).encode("utf-8"),
        )

    def mark_failed(self, correlation_id: str, error: str) -> None:
        out = {"id": correlation_id, "status": "failed", "error": error}
        self.s3.put_object(
            Bucket=self.bucket,
            Key=self._key(correlation_id),
            Body=json.dumps(out).encode("utf-8"),
        )

    def mark_canceled(self, correlation_id: str) -> None:
        # Write a cancel sentinel and update status
        self.s3.put_object(
            Bucket=self.bucket, Key=f"cancels/{correlation_id}", Body=b"1"
        )
        out = {"id": correlation_id, "status": "canceled"}
        self.s3.put_object(
            Bucket=self.bucket,
            Key=self._key(correlation_id),
            Body=json.dumps(out).encode("utf-8"),
        )
