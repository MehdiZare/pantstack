from typing import Optional, Protocol


class User(BaseException):
    pass


class UserRecord:
    def __init__(self, email: str, username: str, password_hash: str, salt: str):
        self.email = email
        self.username = username
        self.password_hash = password_hash
        self.salt = salt


class UserRepository(Protocol):
    def get_by_email(self, email: str) -> Optional[UserRecord]: ...
    def create_user(self, email: str, username: str, password: str) -> UserRecord: ...
    def verify_password(self, rec: UserRecord, password: str) -> bool: ...
