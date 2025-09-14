import base64
import hashlib
import os
import secrets
from typing import Optional

import boto3

from services.auth.domain.ports.users import UserRecord


class DynamoUsers:
    def __init__(self, table_name: str):
        self.table = boto3.resource("dynamodb").Table(table_name)

    @classmethod
    def from_env(cls) -> "DynamoUsers":
        table = os.getenv("AUTH_USERS_TABLE") or "auth-users"
        inst = cls(table)
        # Auto-provision when running against LocalStack to ease local dev
        if os.getenv("LOCALSTACK", "").lower() in ("1", "true", "yes", "on"):
            exceptions = inst.table.meta.client.exceptions
            try:
                inst.table.load()
            except exceptions.ResourceNotFoundException:  # type: ignore[attr-defined]
                inst.table = inst.table.meta.client.create_table(
                    TableName=table,
                    AttributeDefinitions=[
                        {"AttributeName": "pk", "AttributeType": "S"}
                    ],
                    KeySchema=[{"AttributeName": "pk", "KeyType": "HASH"}],
                    BillingMode="PAY_PER_REQUEST",
                )
        return inst

    def _hash(self, password: str, salt: str) -> str:
        dk = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), base64.b64decode(salt), 200_000
        )
        return base64.b64encode(dk).decode()

    def get_by_email(self, email: str) -> Optional[UserRecord]:
        resp = self.table.get_item(Key={"pk": f"USER#{email}"})
        item = resp.get("Item")
        if not item:
            return None
        return UserRecord(
            email=email,
            username=item.get("username", ""),
            password_hash=item["password_hash"],
            salt=item["salt"],
        )

    def create_user(self, email: str, username: str, password: str) -> UserRecord:
        salt = base64.b64encode(secrets.token_bytes(16)).decode()
        ph = self._hash(password, salt)
        self.table.put_item(
            Item={
                "pk": f"USER#{email}",
                "username": username,
                "password_hash": ph,
                "salt": salt,
            },
            ConditionExpression="attribute_not_exists(pk)",
        )
        return UserRecord(email=email, username=username, password_hash=ph, salt=salt)

    def verify_password(self, rec: UserRecord, password: str) -> bool:
        return secrets.compare_digest(self._hash(password, rec.salt), rec.password_hash)
