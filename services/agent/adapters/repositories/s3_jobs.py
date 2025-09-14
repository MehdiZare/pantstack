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
        bucket = (
            os.getenv("STATUS_BUCKET") or os.getenv("BUCKET_NAME") or "agent-status"
        )
        if os.getenv("LOCALSTACK", "").lower() in ("1", "true", "yes", "on"):
            ensure_bucket(aws_client("s3"), bucket_name=bucket)
        return cls(bucket=bucket)

    def _key(self, cid: str) -> str:
        return f"{self.prefix}{cid}.json"

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

    def is_canceled(self, correlation_id: str) -> bool:
        try:
            self.s3.head_object(Bucket=self.bucket, Key=f"cancels/{correlation_id}")
            return True
        except Exception:
            return False
